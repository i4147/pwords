#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def remove_translated_lines(inputfile):
    input_path = Path(inputfile)
    json_path = input_path.with_suffix(".json")
    if not input_path.exists():
        print(f"Error: Input file '{inputfile}' not found.")
        return
    if not json_path.exists():
        print(f"Error: JSON file '{json_path}' not found.")
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return
    translated_abbrs = set()
    for key in translations:
        if "," in key:
            abbr = key.split(",")[0].strip()
            translated_abbrs.add(abbr.upper())
        else:
            translated_abbrs.add(key.strip().upper())
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    remaining_lines = []
    removed_count = 0
    for line in lines:
        stripped_line = line.strip().upper()
        if stripped_line in translated_abbrs:
            removed_count += 1
        else:
            remaining_lines.append(line)
    with open(input_path, "w", encoding="utf-8") as f:
        f.writelines(remaining_lines)
    print(f"Successfully removed {removed_count} translated lines from '{inputfile}'")
    print(f"Remaining lines: {len(remaining_lines)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <inputfile>")
        print("Example: python script.py abbreviations.txt")
        sys.exit(1)
    inputfile = sys.argv[1]
    remove_translated_lines(inputfile)
