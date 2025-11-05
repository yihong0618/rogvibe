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
from textual.containers import Vertical, Horizontal
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
    if len(providers) < 4:
        while len(providers) < 4:
            providers.append("lucky")
    elif 5 <= len(providers) < 8:
        fillers = ["lucky", "handy"]
        filler_index = 0
        while len(providers) < 8:
            providers.append(fillers[filler_index % 2])
            filler_index += 1
    elif len(providers) > 8:
        providers = random.sample(providers, 8)

    return providers


# Prefer detected providers, otherwise fall back to sample names.
DEFAULT_PARTICIPANTS: list[str] = detect_default_participants() or FALLBACK_DEFAULTS

__all__ = [
    "run",
    "run_slot_machine",
    "LotteryApp",
    "LotteryWheel",
    "SpinFinished",
    "SpinTick",
    "SlotMachineApp",
]


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
        border = "yellow" if highlight else "dark_cyan"
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


class SlotReelSpinning(Message):
    """Fired when a reel is spinning."""

    def __init__(self, sender: Widget, reel_index: int, value: str) -> None:
        try:
            super().__init__(sender)  # type: ignore[arg-type]
        except TypeError:
            super().__init__()
        self._origin = sender
        self.reel_index = reel_index
        self.value = value

    @property
    def origin(self) -> Widget:
        """Widget that emitted the message."""
        return self._origin


class SlotReelStopped(Message):
    """Fired when a reel stops spinning."""

    def __init__(self, sender: Widget, reel_index: int, value: str) -> None:
        try:
            super().__init__(sender)  # type: ignore[arg-type]
        except TypeError:
            super().__init__()
        self._origin = sender
        self.reel_index = reel_index
        self.value = value

    @property
    def origin(self) -> Widget:
        """Widget that emitted the message."""
        return self._origin


class SlotAllStopped(Message):
    """Fired when all reels have stopped."""

    def __init__(self, sender: Widget, results: list[str]) -> None:
        try:
            super().__init__(sender)  # type: ignore[arg-type]
        except TypeError:
            super().__init__()
        self._origin = sender
        self.results = results

    @property
    def origin(self) -> Widget:
        """Widget that emitted the message."""
        return self._origin


class SlotMachineReel(Widget):
    """A single reel of the slot machine."""

    DEFAULT_CSS = """
    SlotMachineReel {
        width: 20;
        height: 7;
        border: double $primary;
        content-align: center middle;
        overflow: hidden;
    }
    """

    current_value = reactive("")
    current_index = reactive(0)

    def __init__(self, reel_index: int, items: list[str]) -> None:
        super().__init__()
        self._reel_index = reel_index
        self._items = items
        self._is_spinning = False
        self._timer: Any | None = None
        self._target_value: str | None = None
        self._spin_count = 0
        self.current_index = random.randrange(len(self._items)) if self._items else 0
        self.current_value = self._items[self.current_index] if self._items else "?"

    def render(self) -> Text:
        """Render the reel with scrolling effect showing 3 items."""
        if not self._items:
            return Text("???", justify="center", style="bold yellow")

        # Show 3 items: 1 before, current, 1 after
        indices = [
            (self.current_index - 1) % len(self._items),
            self.current_index,
            (self.current_index + 1) % len(self._items),
        ]

        items = [self._items[i] for i in indices]

        # Create a vertical scrolling effect
        lines = [
            items[0],  # -1
            "┄" * 18,
            items[1],  # current (middle)
            "┄" * 18,
            items[2],  # +1
        ]

        content = "\n".join(lines)
        text = Text(content, justify="center")

        # Calculate positions for styling
        line_lengths = [len(line) + 1 for line in lines]  # +1 for newline

        pos = 0
        # Item -1 (dim)
        text.stylize("dim", pos, pos + len(items[0]))
        pos += line_lengths[0]
        pos += line_lengths[1]  # skip separator

        # Current item (highlighted)
        text.stylize("bold yellow on #444444", pos, pos + len(items[1]))
        pos += line_lengths[2]
        pos += line_lengths[3]  # skip separator

        # Item +1 (dim)
        text.stylize("dim", pos, pos + len(items[2]))

        return text

    def start_spin(self, duration_steps: int) -> None:
        """Start spinning the reel."""
        if self._is_spinning:
            return
        self._is_spinning = True
        self._spin_count = 0
        # Choose target index instead of target value
        self._target_index = random.randrange(len(self._items))
        self._target_value = self._items[self._target_index]
        self._total_steps = duration_steps
        self._initial_delay = 0.03  # Start fast
        self._schedule_spin()

    def _schedule_spin(self) -> None:
        # Calculate dynamic delay - start fast, end slow
        progress = self._spin_count / self._total_steps
        # Use quadratic easing for smooth deceleration
        delay = self._initial_delay + (progress**2) * 0.15
        self._timer = self.set_timer(delay, self._advance_spin)

    def _advance_spin(self) -> None:
        self._spin_count += 1
        # Advance to next index for scrolling effect
        self.current_index = (self.current_index + 1) % len(self._items)
        self.current_value = self._items[self.current_index]
        self.post_message(SlotReelSpinning(self, self._reel_index, self.current_value))

        if self._spin_count >= self._total_steps:
            self._is_spinning = False
            # Set to target index
            self.current_index = self._target_index
            self.current_value = self._items[self.current_index]
            self.post_message(
                SlotReelStopped(self, self._reel_index, self.current_value)
            )
        else:
            self._schedule_spin()

    @property
    def is_spinning(self) -> bool:
        return self._is_spinning

    @property
    def value(self) -> str:
        return self.current_value


class SlotMachineLever(Widget):
    """A lever widget for the slot machine."""

    DEFAULT_CSS = """
    SlotMachineLever {
        width: 8;
        height: auto;
        align: center middle;
    }
    """

    lever_state = reactive("up")  # "up" or "down"

    def render(self) -> Text:
        """Render the lever."""
        if self.lever_state == "up":
            lever_art = """
 ║
 ║
 ●"""
        else:
            lever_art = """

 ║
 ║
 ║
 ●"""
        return Text(lever_art, justify="center", style="bright_cyan")


class SlotMachineWidget(Widget):
    """The complete slot machine with 3 reels and a lever."""

    DEFAULT_CSS = """
    SlotMachineWidget {
        width: auto;
        height: auto;
        align: center middle;
    }
    SlotMachineWidget Horizontal {
        width: auto;
        height: auto;
        align: center middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._items = list(MAYBE_VIBER)
        self._reels = [
            SlotMachineReel(0, self._items),
            SlotMachineReel(1, self._items),
            SlotMachineReel(2, self._items),
        ]
        self._lever = SlotMachineLever()
        self._is_spinning = False
        self._stopped_count = 0
        self._results: list[str] = []

    def compose(self) -> ComposeResult:
        """Compose the slot machine layout with horizontal reels."""
        with Horizontal():
            yield self._reels[0]
            yield self._reels[1]
            yield self._reels[2]
            yield self._lever

    def start_spin(self) -> None:
        """Start spinning all reels with staggered stops."""
        if self._is_spinning:
            return

        self._is_spinning = True
        self._stopped_count = 0
        self._results = []

        # Animate lever pull
        self._lever.lever_state = "down"
        self.refresh()

        # Use a timer to return lever after delay
        def return_lever():
            self._lever.lever_state = "up"
            self.refresh()

        self.set_timer(0.5, return_lever)

        # Start spinning all reels
        for i, reel in enumerate(self._reels):
            # Each reel spins for a different duration (staggered)
            duration = random.randint(30, 50) + i * 20
            reel.start_spin(duration)

    def on_slot_reel_stopped(self, message: SlotReelStopped) -> None:
        """Handle a reel stopping."""
        self._stopped_count += 1
        self._results.append(message.value)

        if self._stopped_count == 3:
            self._is_spinning = False
            self.post_message(SlotAllStopped(self, self._results))

    @property
    def is_spinning(self) -> bool:
        return self._is_spinning


class SlotMachineApp(App):
    """Slot machine app."""

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
        margin-bottom: 1;
    }

    #result {
        height: auto;
        content-align: center middle;
        margin-top: 1;
        color: #ffcc66;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("space", "spin", "Pull Lever"),
        ("enter", "execute", "Run"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._slot_machine = SlotMachineWidget()
        self._result = Static(id="result")
        self._pending_command: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="layout"):
            yield Static(
                "🎰 Press Space to pull the lever; press Enter to run the viber; press q to quit.",
                id="instructions",
            )
            yield self._slot_machine
            yield self._result
        yield Footer()

    def action_spin(self) -> None:
        """Handle spin action."""
        if not self._slot_machine.is_spinning:
            self._pending_command = None
            # Reset reel colors when starting a new spin
            for reel in self._slot_machine._reels:
                reel.styles.border = ("double", "ansi_bright_magenta")
            self._result.update("Pulling lever...")
            self._slot_machine.start_spin()

    def on_slot_all_stopped(self, message: SlotAllStopped) -> None:
        """Handle all reels stopped."""
        results = message.results
        # Count occurrences of each result
        from collections import Counter

        counts = Counter(results)
        # Check if all three are the same - JACKPOT!
        if len(set(results)) == 1:
            winner = results[0]
            self._pending_command = winner
            # Highlight all reels with yellow color for JACKPOT
            for reel in self._slot_machine._reels:
                reel.styles.border = ("heavy", "yellow")
            self._result.update(
                f"🎉🎉🎉 JACKPOT! All three show: {winner} 🎉🎉🎉\n"
                f"↩️  Press Enter to run '{winner}' and exit, or q to quit."
            )
        # Check if two are the same
        elif max(counts.values()) == 2:
            # Find the value that appears twice
            winner = [item for item, count in counts.items() if count == 2][0]
            self._pending_command = winner
            # Highlight matching reels
            for i, reel in enumerate(self._slot_machine._reels):
                if results[i] == winner:
                    reel.styles.border = ("heavy", "yellow")
                else:
                    reel.styles.border = ("double", "ansi_bright_magenta")
            result_text = " | ".join(results)
            self._result.update(
                f"✨ Two match: {winner}! Results: {result_text}\n"
                f"↩️  Press Enter to run '{winner}' and exit, or q to quit."
            )
        else:
            # All different - no match
            # Reset reel colors
            for reel in self._slot_machine._reels:
                reel.styles.border = ("double", "ansi_bright_magenta")
            result_text = " | ".join(results)
            self._result.update(
                f"Results: {result_text}\n"
                f"🔄 Press Space to spin again, or q to quit."
            )

    def action_execute(self) -> None:
        """Execute the winner command."""
        if not self._pending_command:
            return
        self._execute_and_exit(self._pending_command)

    def _execute_and_exit(self, winner: str) -> None:
        """Execute the winner as a command and exit the app."""
        if winner in ("code", "cursor"):
            winner = f"{winner} ."
        argv = shlex.split(winner)
        if not argv:
            self.exit(0)
            return

        cmd = argv[0]
        if shutil.which(cmd) is None:
            print(f"[rogvibe] Command not found: {cmd}")
            self.exit(127)
            return

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


def run_slot_machine() -> None:
    """Launch the slot machine app."""
    app = SlotMachineApp()
    app.run()
