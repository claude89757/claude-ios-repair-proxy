#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys


VERSION_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def normalize_version(raw: str) -> str:
    value = (raw or "").strip()
    match = VERSION_RE.fullmatch(value)
    if not match:
        raise ValueError("version must be SemVer in vX.Y.Z form")
    return f"v{match.group(1)}.{match.group(2)}.{match.group(3)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a Claude iOS release version.")
    parser.add_argument("version", help="Release version, for example v0.1.0")
    args = parser.parse_args(argv)

    try:
        print(normalize_version(args.version))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
