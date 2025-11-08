"""Participant detection utilities."""

from __future__ import annotations

import random
import shutil

from ..constants import MAYBE_VIBER


def detect_default_participants() -> list[str]:
    """Detect available viber commands on the system.

    Returns:
        List of detected providers, shuffled and padded to appropriate size.
        Returns empty list if none found.
    """
    providers: list[str] = []

    fillers = ["lucky", "handy"]

    def on_path(cmd: str) -> bool:
        result = shutil.which(cmd) is not None
        print(f"DEBUG: on_path('{cmd}') -> {result}")
        return result

    for provider in MAYBE_VIBER:
        if on_path(provider):
            providers.append(provider)

    print(f"DEBUG: Initial providers: {providers}, length: {len(providers)}")

    if len(providers) == 0:
        return []

    random.shuffle(providers)
    print(f"DEBUG: After shuffle: {providers}")

    if len(providers) < 4:
        filler_index_less = 0
        while len(providers) < 4:
            providers.append(fillers[filler_index_less % 2])
            filler_index_less += 1
        print(f"DEBUG: After padding to 4: {providers}")
    elif 5 <= len(providers) < 8:
        filler_index = 0
        while len(providers) < 8:
            providers.append(fillers[filler_index % 2])
            filler_index += 1
        print(f"DEBUG: After padding to 8: {providers}")
    elif len(providers) > 8:
        providers = random.sample(providers, 8)
        print(f"DEBUG: After sampling to 8: {providers}")

    print(f"DEBUG: Final result: {providers}, length: {len(providers)}")
    return providers
