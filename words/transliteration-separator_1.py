#!/usr/bin/env python3
"""
Separate transliterated words from a bilingual JSON dictionary.
Usage: python transliteration_separator.py <input_file.json> [--source en] [--target fa]
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import argparse


def detect_transliteration(text: str, source_lang: str = "en", target_lang: str = "fa") -> bool:
    """
    Detect if text contains transliterated content based on language patterns.

    Args:
        text: The text to check
        source_lang: Source language code (e.g., 'en')
        target_lang: Target language code (e.g., 'fa')

    Returns:
        True if text appears to be transliterated
    """
    if not text or not isinstance(text, str):
        return False

    text = text.strip().lower()

    # Language-specific character patterns
    lang_patterns = {
        "fa": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",  # Persian/Arabic script
        "ar": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",  # Arabic script
        "ru": r"[\u0400-\u04FF]",  # Cyrillic
        "el": r"[\u0370-\u03FF]",  # Greek
        "he": r"[\u0590-\u05FF]",  # Hebrew
        "zh": r"[\u4E00-\u9FFF]",  # Chinese
        "ja": r"[\u3040-\u309F\u30A0-\u30FF]",  # Hiragana/Katakana
        "ko": r"[\uAC00-\uD7AF]",  # Korean
        "hi": r"[\u0900-\u097F]",  # Hindi/Devanagari
        "th": r"[\u0E00-\u0E7F]",  # Thai
    }

    # Check if text contains native script characters for target language
    if target_lang in lang_patterns:
        native_pattern = lang_patterns[target_lang]
        has_native = bool(re.search(native_pattern, text))

        # If it has native characters, it's NOT transliterated
        if has_native:
            return False

    # Check for Latin script (transliteration typically uses Latin characters)
    latin_pattern = r"[a-zA-Z]"
    has_latin = bool(re.search(latin_pattern, text))

    if not has_latin:
        return False

    # Additional heuristics for common transliteration patterns

    # Persian/Farsi specific patterns (transliterated from Arabic script)
    if target_lang == "fa":
        # Common Persian transliteration markers
        persian_translit_patterns = [
            r"[kh]gh",
            r"[sh]ch",
            r"aa",
            r"ee",
            r"oo",  # Vowel extensions
            r"\b[a-z]*[khgh][a-z]*\b",  # Words with kh/gh combinations
            r"[aeiou]{2,}",  # Double vowels common in transliteration
        ]

        # If it matches Persian transliteration patterns
        for pattern in persian_translit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # If it's just English words with no Persian-like patterns, likely not transliterated
        common_english_words = {"the", "and", "is", "in", "to", "of", "a", "for", "with", "on"}
        if text in common_english_words:
            return False

    # Arabic specific patterns
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

    # Russian specific patterns (Cyrillic to Latin)
    if target_lang == "ru":
        # Common Russian transliteration patterns
        russian_translit_patterns = [
            r"[sz]h",
            r"yu",
            r"ya",
            r"yo",
            r"zh",
            r"ch",
            r"sh",
            r"yu",
            r"[aeiouy]{2,}",  # Double vowels
            r"\b[a-z]*[khzh][a-z]*\b",  # Words with kh/zh combinations
        ]
        for pattern in russian_translit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

    # Default: if it has Latin characters but no native script for target language,
    # and it's not obviously just source language words, consider it potentially transliterated
    return True


def separate_transliterated_words(
    dictionary: Dict, source_lang: str = "en", target_lang: str = "fa"
) -> Tuple[Dict, Dict]:
    """
    Separate dictionary entries into transliterated and non-transliterated groups.

    Args:
        dictionary: The input dictionary (can be nested or flat)
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Tuple of (transliterated_dict, non_transliterated_dict)
    """
    transliterated = {}
    non_transliterated = {}

    # Handle different dictionary structures
    if isinstance(dictionary, dict):
        for key, value in dictionary.items():
            # Check if the value is transliterated
            if isinstance(value, str):
                is_translit = detect_transliteration(value, source_lang, target_lang)

                if is_translit:
                    transliterated[key] = value
                else:
                    non_transliterated[key] = value
            elif isinstance(value, (list, dict)):
                # Recursively handle nested structures
                sub_translit, sub_non_translit = separate_transliterated_words(value, source_lang, target_lang)

                if sub_translit:
                    transliterated[key] = sub_translit
                if sub_non_translit:
                    non_transliterated[key] = sub_non_translit
            else:
                # Keep other types as-is in non-transliterated
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
                sub_translit, sub_non_translit = separate_transliterated_words(item, source_lang, target_lang)

                if sub_translit:
                    transliterated_list.append(sub_translit)
                if sub_non_translit:
                    non_transliterated_list.append(sub_non_translit)
            else:
                non_transliterated_list.append(item)

        return transliterated_list, non_transliterated_list

    return transliterated, non_transliterated


def process_dictionary_file(input_file: Path, source_lang: str = "en", target_lang: str = "fa") -> None:
    """
    Process a JSON dictionary file and create separated output files.

    Args:
        input_file: Path to the input JSON file
        source_lang: Source language code
        target_lang: Target language code
    """
    print(f"Processing dictionary file: {input_file}")
    print(f"Language pair: {source_lang} -> {target_lang}")

    # Read the input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            dictionary = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_file}': {e}")
        sys.exit(1)

    # Separate transliterated words
    print("Analyzing dictionary entries...")
    transliterated, non_transliterated = separate_transliterated_words(dictionary, source_lang, target_lang)

    # Generate output filenames
    output_dir = input_file.parent
    base_name = input_file.stem

    transliterated_file = output_dir / f"{base_name}_transliterated.json"
    non_transliterated_file = output_dir / f"{base_name}_native.json"

    # Write output files
    print(f"Writing transliterated entries to: {transliterated_file}")
    with open(transliterated_file, "w", encoding="utf-8") as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)

    print(f"Writing native entries to: {non_transliterated_file}")
    with open(non_transliterated_file, "w", encoding="utf-8") as f:
        json.dump(non_transliterated, f, ensure_ascii=False, indent=2)

    # Print statistics
    total_entries = count_entries(dictionary)
    translit_count = count_entries(transliterated)
    native_count = count_entries(non_transliterated)

    print("\n" + "=" * 50)
    print("SEPARATION COMPLETE")
    print("=" * 50)
    print(f"Total entries processed: {total_entries}")
    print(f"Transliterated entries: {translit_count} ({translit_count / total_entries * 100:.1f}%)")
    print(f"Native script entries: {native_count} ({native_count / total_entries * 100:.1f}%)")
    print("=" * 50)


def count_entries(data) -> int:
    """Count the total number of leaf entries in a nested structure."""
    if isinstance(data, str):
        return 1
    elif isinstance(data, list):
        return sum(count_entries(item) for item in data)
    elif isinstance(data, dict):
        return sum(count_entries(value) for value in data.values())
    else:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Separate transliterated words from a bilingual JSON dictionary")
    parser.add_argument("input_file", help="Input JSON dictionary file")
    parser.add_argument("--source", default="en", help="Source language code (default: en)")
    parser.add_argument("--target", default="fa", help="Target language code (default: fa)")

    args = parser.parse_args()

    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    process_dictionary_file(input_file, args.source, args.target)


if __name__ == "__main__":
    main()
