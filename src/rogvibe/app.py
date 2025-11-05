from __future__ import annotations

import os
import sys
import random
import shlex
import shutil
from contextlib import nullcontext
from typing import Iterable, Sequence, Any

from rich import box
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Static

from .config import MAYBE_VIBER

FALLBACK_DEFAULTS: list[str] = [
    "handy",
    "handy",
    "handy",
    "handy",
]


def detect_default_participants() -> list[str]:
    providers: list[str] = []

    def on_path(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    for provider in MAYBE_VIBER:
        if on_path(provider):
            providers.append(provider)
    random.shuffle(providers)
    # 如果不足4个,用 "lucky" 补齐到4个
    if len(providers) < 4:
        while len(providers) < 4:
            providers.append("lucky")
    # 如果大于等于5个小于8个,用 "lucky" 或 "handy" 补齐到8个
    elif 5 <= len(providers) < 8:
        fillers = ["lucky", "handy"]
        filler_index = 0
        while len(providers) < 8:
            providers.append(fillers[filler_index % 2])
            filler_index += 1
    # 如果大于8个,只随机取其中的8个
    elif len(providers) > 8:
        providers = random.sample(providers, 8)

    return providers


# Prefer detected providers, otherwise fall back to sample names.
DEFAULT_PARTICIPANTS: list[str] = detect_default_participants() or FALLBACK_DEFAULTS

__all__ = ["run", "LotteryApp", "LotteryWheel", "SpinFinished", "SpinTick"]


class SpinFinished(Message):
    """Fired when the wheel stops spinning."""

    def __init__(self, sender: Widget, winner: str) -> None:
        try:
            super().__init__(sender)  # type: ignore[arg-type]  # Textual <=0.43 expects the sender argument.
        except TypeError:
            super().__init__()  # Newer Textual versions no longer take sender.
        self._origin = sender
        self.winner = winner

    @property
    def origin(self) -> Widget:
        """Widget that emitted the message."""
        return self._origin


class SpinTick(Message):
    """Fired each time the wheel advances during spinning."""

    def __init__(self, sender: Widget, dice_face: str) -> None:
        try:
            super().__init__(sender)  # type: ignore[arg-type]
        except TypeError:
            super().__init__()
        self._origin = sender
        self.dice_face = dice_face

    @property
    def origin(self) -> Widget:
        """Widget that emitted the message."""
        return self._origin


class LotteryWheel(Widget):
    """Simple wheel that highlights one participant at a time.

    Layout auto-adjusts by participant count with a minimum of 4:
    - 4 or fewer (but >=4): 2x2 grid (4 visible slots)
    - 5 to 8: 3x3 grid with a bullseye center (8 visible slots)
    """

    DEFAULT_CSS = """
    LotteryWheel {
        width: 50;
        height: auto;
    }
    """

    current_index = reactive(0)
    current_dice = reactive("🎯")

    def __init__(self, participants: Sequence[str]) -> None:
        if not participants or len(participants) < 4:
            raise ValueError("Provide at least 4 participants.")

        super().__init__()

        # Determine grid size and visible capacity
        self._grid_size = 2 if len(participants) <= 4 else 3
        self._capacity = 4 if self._grid_size == 2 else 8
        self._cell_width = 12 if self._grid_size == 2 else 14

        limited = list(participants[: self._capacity])
        self._participants = limited
        self._participant_count = len(self._participants)
        extra = len(participants) - len(self._participants)
        self._truncated = extra > 0
        if self._truncated:
            self._extra_count = extra
        # Slot indices around the perimeter in clockwise order
        self._layout_slots: list[int | None] = [
            idx if idx < self._participant_count else None
            for idx in range(self._capacity)
        ]
        self._is_spinning = False
        self._steps_remaining = 0
        self._initial_steps = 0
        self._delay = 0.08
        self._timer: Any | None = None
        self._dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        self._emoji_dice = "🎲"

    def on_mount(self) -> None:
        """Adjust width for nicer layout depending on grid size."""
        # Narrower width for 2x2 so it doesn't look sparse
        self.styles.width = 36 if self._grid_size == 2 else 50

    def render(self) -> Panel:
        """Render participants in a faux wheel layout."""
        table = Table.grid(expand=False, padding=(0, 2))

        if self._grid_size == 2:
            # 2x2 grid: slots arranged clockwise
            table.add_row(self._render_cell(0), self._render_cell(1))
            table.add_row(self._render_cell(3), self._render_cell(2))
        else:
            # 3x3 grid: perimeter slots with bullseye center
            table.add_row(
                self._render_cell(0), self._render_cell(1), self._render_cell(2)
            )
            table.add_row(
                self._render_cell(7),
                Panel(
                    Text(self.current_dice, justify="center"),
                    box=box.MINIMAL,
                    padding=(0, 2),
                ),
                self._render_cell(3),
            )
            table.add_row(
                self._render_cell(6), self._render_cell(5), self._render_cell(4)
            )

        return Panel(
            Align.center(table),
            title="Rogvibe",
            border_style="bright_cyan",
            box=box.ROUNDED,
        )

    def _render_cell(self, slot_index: int) -> Panel:
        participant_index = self._layout_slots[slot_index]
        if participant_index is None:
            return Panel(
                "",
                box=box.SQUARE,
                width=self._cell_width,
                padding=(0, 1),
                border_style="dim",
            )

        participant = self._participants[participant_index]
        label = Text(participant, justify="center", overflow="ellipsis")
        highlight = participant_index == self.current_index
        border = "gold1" if highlight else "dark_cyan"
        style = "black on yellow" if highlight else "white on dark_blue"
        label.stylize(style)
        return Panel(
            label,
            box=box.SQUARE,
            width=self._cell_width,
            padding=(0, 1),
            border_style=border,
        )

    def start_spin(self) -> None:
        if self._is_spinning:
            return

        self._is_spinning = True
        self.current_dice = "🎲"  # 开始旋转时显示骰子
        self._initial_steps = random.randint(
            self._participant_count * 4, self._participant_count * 7
        )
        target_index = random.randrange(self._participant_count)
        offset = (target_index - self.current_index) % self._participant_count
        self._steps_remaining = self._initial_steps + offset
        self._delay = 0.05
        self._schedule_tick()

    def _schedule_tick(self) -> None:
        self._timer = self.set_timer(self._delay, self._advance)

    def _advance(self) -> None:
        self.current_index = (self.current_index + 1) % self._participant_count
        self._steps_remaining -= 1
        # 随机切换骰子面,让它"旋转"起来
        dice_face = random.choice(self._dice_faces)
        self.current_dice = dice_face
        # 发送消息通知骰子变化(也发送字符骰子面)
        self.post_message(SpinTick(self, dice_face))

        if self._steps_remaining <= 0:
            self._is_spinning = False
            self.current_dice = "🎯"  # 停止时回到靶心
            winner = self._participants[self.current_index]
            self.post_message(SpinFinished(self, winner))
            return

        progress = 1 - self._steps_remaining / self._initial_steps
        self._delay = 0.05 + progress * progress * 0.25
        self._schedule_tick()

    @property
    def is_spinning(self) -> bool:
        return self._is_spinning

    @property
    def truncated(self) -> bool:
        return self._truncated

    @property
    def extra_count(self) -> int:
        return getattr(self, "_extra_count", 0)

    @property
    def visible_capacity(self) -> int:
        """Number of names that can be shown at once based on layout."""
        return self._capacity


class LotteryApp(App):
    """App wiring the wheel and some helper text together."""

    CSS = """
    Screen {
        align: center middle;
        background: #1b1e28;
    }

    #layout {
        width: auto;
        align: center middle;
        padding: 1 4;
        border: tall #3f6fb5;
    }

    #instructions {
        content-align: center middle;
        text-style: bold;
    }

    #warning {
        color: #ffcc66;
        text-style: italic;
        margin-top: 1;
    }

    #result {
        height: auto;
        content-align: center middle;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("space", "spin", "Spin"),
        ("enter", "execute", "Run"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, participants: Sequence[str]) -> None:
        super().__init__()
        self._participants = list(participants)
        self._wheel = LotteryWheel(self._participants)
        self._result = Static(id="result")
        self._pending_command: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="layout"):
            yield Static(
                "Press Space to spin; press Enter to run the viber; press q to quit.",
                id="instructions",
            )
            if self._wheel.truncated:
                yield Static(
                    f"⚠️ Showing only the first {self._wheel.visible_capacity} names; the remaining {self._wheel.extra_count} are ignored.",
                    id="warning",
                )
            yield self._wheel
            yield self._result
        yield Footer()

    def action_spin(self) -> None:
        if not self._wheel.is_spinning:
            self._pending_command = None
            self._result.update("🎲 Spinning...")
            self._wheel.start_spin()

    def on_spin_tick(self, message: SpinTick) -> None:
        """Update the spinning message with animated dice."""
        dice_emoji_map = {"⚀": "⚀", "⚁": "⚁", "⚂": "⚂", "⚃": "⚃", "⚄": "⚄", "⚅": "⚅"}
        dice_display = dice_emoji_map.get(message.dice_face, "🎲")
        self._result.update(f"{dice_display} Spinning...")

    def on_spin_finished(self, message: SpinFinished) -> None:
        self._pending_command = message.winner
        # 如果是 "lucky" 或 "handy",不允许执行命令
        if message.winner in ("lucky", "handy"):
            self._result.update(
                f"🎉 viber: {message.winner}\n🍀 Lucky winner! Press Space to spin again, or q to quit."
            )
        else:
            self._result.update(
                f"🎉 viber: {message.winner}\n↩️  Press Enter to run and exit, or q to quit."
            )

    def action_execute(self) -> None:
        if not self._pending_command:
            return
        # 如果是 "lucky" 或 "handy",不执行命令
        if self._pending_command in ("lucky", "handy"):
            return
        self._execute_and_exit(self._pending_command)

    def _execute_and_exit(self, winner: str) -> None:
        """Execute the winner as a command and exit the app.

        - Parses the winner string with shlex to support simple arguments.
        - If command is not on PATH, exits with code 127.
        - On success, replaces the current process using os.execvp.
        """
        # 如果是 code 或 cursor,自动添加 '.' 参数
        if winner in ("code", "cursor"):
            winner = f"{winner} ."
        argv = shlex.split(winner)
        if not argv:
            self.exit(0)
            return

        cmd = argv[0]
        if shutil.which(cmd) is None:
            # Print to stderr-like stream and exit with 127 (command not found)
            print(f"[rogvibe] Command not found: {cmd}")
            self.exit(127)
            return

        # Replace current process with the chosen command.
        # Use Textual's suspend() to restore terminal state before exec.
        ctx = self.suspend() if hasattr(self, "suspend") else nullcontext()
        try:
            with ctx:
                os.execvp(cmd, argv)
        except FileNotFoundError:
            print(f"[rogvibe] Command not found: {cmd}", file=sys.stderr)
            self.exit(127)
        except PermissionError:
            print(f"[rogvibe] Permission denied: {cmd}", file=sys.stderr)
            self.exit(126)
        except OSError as e:
            print(f"[rogvibe] Failed to exec '{cmd}': {e}", file=sys.stderr)
            self.exit(1)


def run(participants: Iterable[str] | None = None) -> None:
    """Launch the Textual app with the provided participants."""
    normalized = (
        [name.strip() for name in participants if name.strip()] if participants else []
    )
    names = normalized or list(DEFAULT_PARTICIPANTS)
    app = LotteryApp(names)
    app.run()
