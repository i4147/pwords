#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def extract_uppercase_abbreviations(inputfile):
    input_path = Path(inputfile)
    if not input_path.exists():
        print(f"Error: Input file '{inputfile}' not found.")
        return
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return
    abbreviations = {}
    regular_translations = {}
    for key, value in data.items():
        if "," in key:
            english_part = key.split(",")[0].strip()
        else:
            english_part = key.strip()
        if english_part.isupper() and any(c.isalpha() for c in english_part):
            abbreviations[key] = value
        else:
            regular_translations[key] = value
    abbr_path = input_path.parent / "abbreviations.json"
    if abbreviations:
        with open(abbr_path, "w", encoding="utf-8") as f:
            json.dump(abbreviations, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(abbreviations)} abbreviations to '{abbr_path}'")
    else:
        print("No uppercase abbreviations found.")
        with open(abbr_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(regular_translations, f, ensure_ascii=False, indent=2)
    print(f"Updated '{inputfile}' with {len(regular_translations)} remaining translations")
    print(
        f"Summary: {len(abbreviations)} abbreviations extracted, {len(regular_translations)} regular translations kept"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <inputfile.json>")
        print("Example: python extract_abbreviations.py translations.json")
        sys.exit(1)
    inputfile = sys.argv[1]
    extract_uppercase_abbreviations(inputfile)
