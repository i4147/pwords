#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def detect_transliteration(
    text: str, source_lang: str = "en", target_lang: str = "fa"
) -> bool:
    if not text or not isinstance(text, str):
        return False
    text = text.strip().lower()
    lang_patterns = {
        "fa": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",
        "ar": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",
        "ru": r"[\u0400-\u04FF]",
        "el": r"[\u0370-\u03FF]",
        "he": r"[\u0590-\u05FF]",
        "zh": r"[\u4E00-\u9FFF]",
        "ja": r"[\u3040-\u309F\u30A0-\u30FF]",
        "ko": r"[\uAC00-\uD7AF]",
        "hi": r"[\u0900-\u097F]",
        "th": r"[\u0E00-\u0E7F]",
    }
    if target_lang in lang_patterns:
        native_pattern = lang_patterns[target_lang]
        has_native = bool(re.search(native_pattern, text))
        if has_native:
            return False
    latin_pattern = r"[a-zA-Z]"
    has_latin = bool(re.search(latin_pattern, text))
    if not has_latin:
        return False
    if target_lang == "fa":
        persian_translit_patterns = [
            r"[kh]gh",
            r"[sh]ch",
            r"aa",
            r"ee",
            r"oo",
            r"\b[a-z]*[khgh][a-z]*\b",
            r"[aeiou]{2,}",
        ]
        for pattern in persian_translit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        common_english_words = {
            "the",
            "and",
            "is",
            "in",
            "to",
            "of",
            "a",
            "for",
            "with",
            "on",
        }
        if text in common_english_words:
            return False
    if target_lang == "ar":
        arabic_translit_patterns = [
            r"[kh]gh",
            r"[sh]ch",
            r"aa",
            r"ee",
            r"oo",
            r"\b[a-z]*[khgh][a-z]*\b",
        ]
        for pattern in arabic_translit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
    if target_lang == "ru":
        russian_translit_patterns = [
            r"[sz]h",
            r"yu",
            r"ya",
            r"yo",
            r"zh",
            r"ch",
            r"sh",
            r"yu",
            r"[aeiouy]{2,}",
            r"\b[a-z]*[khzh][a-z]*\b",
        ]
        for pattern in russian_translit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
    return True


def separate_transliterated_words(
    dictionary: dict, source_lang: str = "en", target_lang: str = "fa"
) -> tuple[dict, dict]:
    transliterated = {}
    non_transliterated = {}
    if isinstance(dictionary, dict):
        for key, value in dictionary.items():
            if isinstance(value, str):
                is_translit = detect_transliteration(value, source_lang, target_lang)
                if is_translit:
                    transliterated[key] = value
                else:
                    non_transliterated[key] = value
            elif isinstance(value, (list, dict)):
                sub_translit, sub_non_translit = separate_transliterated_words(
                    value, source_lang, target_lang
                )
                if sub_translit:
                    transliterated[key] = sub_translit
                if sub_non_translit:
                    non_transliterated[key] = sub_non_translit
            else:
                non_transliterated[key] = value
    elif isinstance(dictionary, list):
        transliterated_list = []
        non_transliterated_list = []
        for item in dictionary:
            if isinstance(item, str):
                is_translit = detect_transliteration(item, source_lang, target_lang)
                if is_translit:
                    transliterated_list.append(item)
                else:
                    non_transliterated_list.append(item)
            elif isinstance(item, (list, dict)):
                sub_translit, sub_non_translit = separate_transliterated_words(
                    item, source_lang, target_lang
                )
                if sub_translit:
                    transliterated_list.append(sub_translit)
                if sub_non_translit:
                    non_transliterated_list.append(sub_non_translit)
            else:
                non_transliterated_list.append(item)
        return transliterated_list, non_transliterated_list
    return transliterated, non_transliterated


def process_dictionary_file(
    input_file: Path, source_lang: str = "en", target_lang: str = "fa"
) -> None:
    print(f"Processing dictionary file: {input_file}")
    print(f"Language pair: {source_lang} -> {target_lang}")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            dictionary = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_file}': {e}")
        sys.exit(1)
    print("Analyzing dictionary entries...")
    transliterated, non_transliterated = separate_transliterated_words(
        dictionary, source_lang, target_lang
    )
    output_dir = input_file.parent
    base_name = input_file.stem
    transliterated_file = output_dir / f"{base_name}_transliterated.json"
    non_transliterated_file = output_dir / f"{base_name}_native.json"
    print(f"Writing transliterated entries to: {transliterated_file}")
    with open(transliterated_file, "w", encoding="utf-8") as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"Writing native entries to: {non_transliterated_file}")
    with open(non_transliterated_file, "w", encoding="utf-8") as f:
        json.dump(non_transliterated, f, ensure_ascii=False, indent=2)
    total_entries = count_entries(dictionary)
    translit_count = count_entries(transliterated)
    native_count = count_entries(non_transliterated)
    print("\n" + "=" * 50)
    print("SEPARATION COMPLETE")
    print("=" * 50)
    print(f"Total entries processed: {total_entries}")
    print(
        f"Transliterated entries: {translit_count} ({translit_count / total_entries * 100:.1f}%)"
    )
    print(
        f"Native script entries: {native_count} ({native_count / total_entries * 100:.1f}%)"
    )
    print("=" * 50)


def count_entries(data) -> int:
    if isinstance(data, str):
        return 1
    elif isinstance(data, list):
        return sum(count_entries(item) for item in data)
    elif isinstance(data, dict):
        return sum(count_entries(value) for value in data.values())
    else:
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Separate transliterated words from a bilingual JSON dictionary"
    )
    parser.add_argument("input_file", help="Input JSON dictionary file")
    parser.add_argument(
        "--source", default="en", help="Source language code (default: en)"
    )
    parser.add_argument(
        "--target", default="fa", help="Target language code (default: fa)"
    )
    args = parser.parse_args()
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    process_dictionary_file(input_file, args.source, args.target)


if __name__ == "__main__":
    main()
