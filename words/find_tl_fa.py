#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import re
import sys
import unicodedata
from multiprocessing import Pool
from pathlib import Path


def normalize_persian(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ؤ": "و",
        "ئ": "ی",
        "ء": "",
        "ٔ": "",
        "ٰ": "",
        "ً": "",
        "ٌ": "",
        "ٍ": "",
        "َ": "",
        "ُ": "",
        "ِ": "",
        "ّ": "",
        "ْ": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("ـ", "").replace("\u200c", " ").replace("\u200d", "")
    return text.strip()


def transliterate_persian_to_english(persian_word):
    mapping = {
        "ا": "a",
        "آ": "a",
        "ب": "b",
        "پ": "p",
        "ت": "t",
        "ث": "s",
        "ج": "j",
        "چ": "ch",
        "ح": "h",
        "خ": "kh",
        "د": "d",
        "ذ": "z",
        "ر": "r",
        "ز": "z",
        "ژ": "zh",
        "س": "s",
        "ش": "sh",
        "ص": "s",
        "ض": "z",
        "ط": "t",
        "ظ": "z",
        "ع": "a",
        "غ": "gh",
        "ف": "f",
        "ق": "gh",
        "ک": "k",
        "گ": "g",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "و": "v",
        "ه": "h",
        "ی": "y",
        "ي": "y",
        "ك": "k",
        " ": " ",
    }
    result = []
    persian_normalized = normalize_persian(persian_word)
    for char in persian_normalized:
        if char in mapping:
            result.append(mapping[char])
        elif char == " ":
            result.append(" ")
    return "".join(result).strip()


def is_transliteration(persian_word, translation):
    if not translation or not persian_word:
        return False
    persian_norm = normalize_persian(persian_word)
    trans_norm = translation.lower().strip()
    trans_clean = re.sub(r"^(the|a|an|to|of|for|in|on|at|by)\s+", "", trans_norm)
    expected_translit = transliterate_persian_to_english(persian_norm).lower()
    if trans_clean == expected_translit:
        return True
    if len(trans_clean) > 2 and len(expected_translit) > 2:
        if trans_clean.replace(" ", "") == expected_translit.replace(" ", ""):
            return True
        variations = {
            "ou": "u",
            "oo": "u",
            "ee": "i",
            "ea": "i",
            "gh": "q",
            "kh": "x",
            "sh": "sh",
            "ch": "ch",
        }
        clean_trans = trans_clean
        clean_expected = expected_translit
        for old, new in variations.items():
            clean_trans = clean_trans.replace(old, new)
            clean_expected = clean_expected.replace(old, new)
        if clean_trans == clean_expected:
            return True
    persian_chars = set("اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیي ")
    if (
        all(c in persian_chars or c in " -" for c in persian_norm)
        and (
            all(c not in persian_chars for c in trans_norm)
            and len(trans_norm) < len(persian_norm) * 2
        )
        and re.match(r"^[a-z\s\'-]+$", trans_norm)
    ):
        common_english = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "shall",
            "should",
            "may",
            "might",
            "must",
            "can",
            "could",
            "of",
            "in",
            "on",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "from",
            "up",
            "down",
            "out",
            "off",
            "over",
            "under",
        }
        if trans_norm not in common_english:
            return True
    return False


def check_entry(args):
    persian_word, translation = args
    try:
        if is_transliteration(persian_word, translation):
            return (persian_word, translation, True)
        else:
            return (persian_word, translation, False)
    except Exception as e:
        print(f"Error processing '{persian_word}': {e}", file=sys.stderr)
        return (persian_word, translation, False)


def process_json_file(input_file):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    print(f"Reading {input_path}...")
    try:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    if not isinstance(data, dict):
        print("Error: JSON file should contain a dictionary of Persian-English pairs.")
        sys.exit(1)
    print(f"Found {len(data)} entries. Processing...")
    entries = list(data.items())
    with Pool(processes=8) as pool:
        results = pool.map(check_entry, entries)
    transliterated = {}
    cleaned = {}
    for persian_word, translation, is_translit in results:
        if is_translit:
            transliterated[persian_word] = translation
        else:
            cleaned[persian_word] = translation
    return transliterated, cleaned


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input.json>")
        sys.exit(1)
    input_file = sys.argv[1]
    transliterated, cleaned = process_json_file(input_file)
    input_path = Path(input_file)
    output_dir = input_path.parent
    transliterated_path = output_dir / "transliterated.json"
    cleaned_path = output_dir / "cleaned.json"
    print(f"\nResults:")
    print(f"  - Total entries: {len(transliterated) + len(cleaned)}")
    print(f"  - Transliterated entries: {len(transliterated)}")
    print(f"  - Cleaned entries: {len(cleaned)}")
    with transliterated_path.open("w", encoding="utf-8") as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"  - Saved transliterated entries to: {transliterated_path}")
    with cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"  - Saved cleaned entries to: {cleaned_path}")
    if transliterated:
        print("\nExamples of detected transliterations:")
        for _i, (persian, trans) in enumerate(list(transliterated.items())[:10]):
            print(f"  {persian} -> {trans}")
        if len(transliterated) > 10:
            print(f"  ... and {len(transliterated) - 10} more")


if __name__ == "__main__":
    main()
