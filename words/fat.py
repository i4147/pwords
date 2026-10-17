#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from multiprocessing import Pool
from pathlib import Path


WORKERS = 8

# Persian/Arabic characters mapped to approximate Latin sounds.
PERSIAN_TO_LATIN = {
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
    "ع": "",
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
    "ی": "y",
    "ئ": "y",
    "ء": "",
    "ؤ": "v",
}

# Characters that should be ignored when normalizing Persian text.
PERSIAN_MARKS = {
    "\u064b",  # fathatan
    "\u064c",  # dammatan
    "\u064d",  # kasratan
    "\u064e",  # fatha
    "\u064f",  # damma
    "\u0650",  # kasra
    "\u0651",  # shadda
    "\u0652",  # sukun
    "\u0670",  # dagger alif
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
}

# Detect if text contains Persian/Arabic characters
PERSIAN_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
NON_LATIN_RE = re.compile(r"[^a-z]")
LATIN_RE = re.compile(r"[^a-z]+")


def normalize_persian(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    replacements = {
        "ی": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
    }

    text = "".join(replacements.get(char, char) for char in text)
    text = "".join(char for char in text if char not in PERSIAN_MARKS)

    return text


def transliterate_persian(text: str) -> str:
    """Create a rough phonetic Latin representation of Persian text."""
    text = normalize_persian(text)

    result = []
    for char in text:
        result.append(PERSIAN_TO_LATIN.get(char, char))

    value = "".join(result).lower()
    value = NON_LATIN_RE.sub("", value)

    # Collapse common transliteration variations.
    replacements = (
        ("ou", "u"),
        ("oo", "u"),
        ("ee", "i"),
        ("ei", "i"),
        ("ey", "i"),
        ("ay", "ai"),
        ("aa", "a"),
        ("kh", "x"),
        ("gh", "q"),
        ("sh", "š"),
        ("ch", "č"),
        ("zh", "ž"),
    )

    for old, new in replacements:
        value = value.replace(old, new)

    return value


def normalize_english(text: str) -> str:
    """Normalize an English translation for comparison."""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    return LATIN_RE.sub("", text)


def remove_vowels(text: str) -> str:
    return re.sub(r"[aeiou]", "", text)


def looks_like_abbreviation(value: str) -> bool:
    """Avoid flagging likely abbreviations such as CPU, NASA, or HTML."""
    value = str(value).strip()

    if not value:
        return True

    # Original uppercase abbreviations.
    if value.isupper() and len(value) <= 12:
        return True

    # Dotted abbreviations: U.S.A., Ph.D., etc.
    if re.fullmatch(r"(?:[A-Za-z]\.){2,}", value):
        return True

    # Very short values are usually abbreviations or initials.
    normalized = normalize_english(value)
    return len(normalized) <= 2


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0

    direct = SequenceMatcher(None, left, right).ratio()

    left_no_vowels = remove_vowels(left)
    right_no_vowels = remove_vowels(right)

    consonant_similarity = SequenceMatcher(
        None,
        left_no_vowels,
        right_no_vowels,
    ).ratio()

    return max(direct, consonant_similarity)


def is_probable_transliteration(item: tuple[str, object]) -> bool:
    """
    Return True when value is probably a phonetic spelling of key.

    The JSON is expected to contain:
        {"Persian word": "English translation"}
    """
    key, value = item

    if not isinstance(key, str) or not isinstance(value, str):
        return False

    key = key.strip()
    value = value.strip()

    if not key or not value:
        return False

    # Validate that key contains Persian/Arabic characters
    if not PERSIAN_CHAR_RE.search(key):
        return False

    # Do not treat Persian explanations or multi-word translations
    # as transliterations.
    if any(char in value for char in "،؛؟"):
        return False

    # Ignore values containing non-Latin letters.
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ._/'-]*", value):
        return False

    if looks_like_abbreviation(value):
        return False

    english = normalize_english(value)
    phonetic = transliterate_persian(key)

    if not english or not phonetic:
        return False

    score = similarity(phonetic, english)

    # Exact or nearly exact phonetic match.
    if english == phonetic:
        return True

    if len(english) >= 5 and score >= 0.82:
        return True

    # Strong consonant match catches transliterations with different vowels.
    if len(english) >= 6:
        consonant_score = similarity(
            remove_vowels(phonetic),
            remove_vowels(english),
        )
        if consonant_score >= 0.90:
            return True

    return False


def check_item(item: tuple[str, object]) -> tuple[str, bool]:
    return item[0], is_probable_transliteration(item)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} INPUT.json", file=sys.stderr)
        raise SystemExit(2)

    input_path = Path(sys.argv[1])

    if not input_path.is_file():
        print(f"Error: file does not exist: {input_path}", file=sys.stderr)
        raise SystemExit(1)

    with input_path.open("r", encoding="utf-8") as file:
        data = json.loads(file.read())

    if not isinstance(data, dict):
        print("Error: the top-level JSON value must be an object.", file=sys.stderr)
        raise SystemExit(1)

    items = list(data.items())

    # Pool.map preserves input order.
    with Pool(processes=WORKERS) as pool:
        results = pool.map(check_item, items, chunksize=1000)

    transliterated = {}
    cleaned = {}

    for key, is_transliteration in results:
        value = data[key]

        if is_transliteration:
            transliterated[key] = value
        else:
            cleaned[key] = value

    transliterated_path = input_path.with_name("transliterated.json")
    cleaned_path = input_path.with_name("cleaned.json")

    with transliterated_path.open("w", encoding="utf-8") as file:
        json.dump(
            transliterated,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    with cleaned_path.open("w", encoding="utf-8") as file:
        json.dump(
            cleaned,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Input records:          {len(data):,}")
    print(f"Transliterated records: {len(transliterated):,}")
    print(f"Cleaned records:        {len(cleaned):,}")
    print(f"Written: {transliterated_path}")
    print(f"Written: {cleaned_path}")


if __name__ == "__main__":
    main()
