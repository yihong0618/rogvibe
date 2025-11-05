from __future__ import annotations

import sys
from typing import Sequence

from .app import run


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint invoked via `python -m rogvibe` or project scripts."""
    args = list(argv) if argv is not None else sys.argv[1:]
    run(args or None)


if __name__ == "__main__":
    main()
