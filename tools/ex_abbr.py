#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint


def extract_uppercase_abbreviations(inputfile):
    path = Path(inputfile)
    lines: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    abbreviations = []
    regular_lines = []
    for line in lines:
        en = line.strip()
        if en.isupper() and any(c.isalpha() for c in en):
            abbreviations.append(line)
            cprint(line)
        else:
            regular_lines.append(line)
    abbr_path = path.parent / "abbrevi.txt"
    if abbreviations:
        with open(abbr_path, "a", encoding="utf-8") as f:
            for k in abbreviations:
                f.write(f"{k}\n")
    with open(path, "w", encoding="utf-8") as f:
        for k in regular_lines:
            f.write(f"{k}\n")
    print(f"Updated '{inputfile}' with {len(regular_lines)} remaining translations")
    print(f"Summary: {len(abbreviations)} abbreviations extracted, {len(regular_lines)} regular translations kept")


if __name__ == "__main__":
    inputfile = sys.argv[1]
    extract_uppercase_abbreviations(inputfile)
