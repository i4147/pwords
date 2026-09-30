from __future__ import annotations

import json
import sys
from pathlib import Path


def create_dictionary_json(english_filepath: Path, persian_filepath: Path, output_json_path: Path):
    if not english_filepath.is_file():
        print(f"Error: English file not found at {english_filepath}", file=sys.stderr)
        sys.exit(1)
    if not persian_filepath.is_file():
        print(f"Error: Persian file not found at {persian_filepath}", file=sys.stderr)
        sys.exit(1)

    eng_words = []
    persian_translations = []

    try:
        with english_filepath.open("r", encoding="utf-8") as f_eng:
            for line in f_eng:
                word = line.strip()
                if word:
                    eng_words.append(word)

        with persian_filepath.open("r", encoding="utf-8") as f_fa:
            for line in f_fa:
                translation = line.strip()
                if translation:
                    persian_translations.append(translation)

    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        sys.exit(1)

    if len(eng_words) != len(persian_translations):
        print(
            f"Warning: Number of English words ({len(eng_words)}) does not match "
            f"number of Persian translations ({len(persian_translations)}). "
            f"The output might be incomplete or mismatched.",
            file=sys.stderr,
        )
        min_len = min(len(eng_words), len(persian_translations))
        eng_words = eng_words[:min_len]
        persian_translations = persian_translations[:min_len]

    dictionary_list = []
    for i in range(len(eng_words)):
        dictionary_list.append({eng_words[i]: persian_translations[i]})

    try:
        with output_json_path.open("w", encoding="utf-8") as f_out:
            json.dump(dictionary_list, f_out, ensure_ascii=False, indent=4)
        print(f"Successfully created dictionary JSON at: {output_json_path}")
    except Exception as e:
        print(f"Error saving JSON file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python script_name.py <english_words_file> <persian_translations_file>")
        sys.exit(1)

    english_file = Path(sys.argv[1])
    persian_file = Path(sys.argv[2])
    output_file = Path("dic.json")

    create_dictionary_json(english_file, persian_file, output_file)


if __name__ == "__main__":
    main()
