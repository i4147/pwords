from __future__ import annotations

import json
import mmap
import re
import sys
from multiprocessing import Pool
from pathlib import Path

PERSIAN_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def is_transliteration(persian_word: str, english_word: str) -> bool:
    if not english_word or not persian_word:
        return False

    if not re.fullmatch(r"[a-zA-Z]+", english_word):
        return False

    if not PERSIAN_RE.search(persian_word):
        return False

    eng = english_word.lower()

    if not (2 <= len(eng) <= 20):
        return False

    eng_vowels = sum(1 for c in eng if c in VOWELS)
    eng_consonants = sum(1 for c in eng if c in CONSONANTS)

    if eng_vowels == 0 or eng_consonants == 0:
        return False

    transliteration_patterns = [
        r"kh",
        r"sh",
        r"ch",
        r"gh",
        r"zh",
        r"oo",
        r"ee",
        r"aa",
        r"ii",
        r"uu",
        r"ae",
        r"oe",
        r"ue",
    ]
    for pattern in transliteration_patterns:
        if re.search(pattern, eng):
            return True

    if re.search(r"(.)\1{1,}", eng):
        return True

    persian_suffixes = ["eh", "ah", "ih", "uh", "yeh", "veh", "deh", "reh"]
    for suffix in persian_suffixes:
        if eng.endswith(suffix):
            return True

    persian_prefixes = ["al", "el", "ol", "ul", "be", "de", "ke", "me", "ne", "re", "se", "te"]
    for prefix in persian_prefixes:
        if eng.startswith(prefix):
            return True

    return bool(len(eng) <= 3 and len(persian_word) > 3)


def process_chunk(chunk_data: tuple) -> list:
    (chunk,) = chunk_data
    transliterated = []
    for key, value in chunk:
        if isinstance(value, str) and is_transliteration(key, value):
            transliterated.append(key)
    return transliterated


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File {input_path} not found")
        sys.exit(1)

    with open(input_path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        data = json.loads(mm.read().decode("utf-8"))

    if not isinstance(data, dict):
        print("Error: Input JSON must be a dictionary")
        sys.exit(1)

    items = list(data.items())
    total = len(items)
    print(f"Loaded {total} entries from {input_path}")

    num_workers = 8
    chunk_size = max(1, total // (num_workers * 4))
    chunks = []
    for i in range(0, total, chunk_size):
        chunks.append(items[i : i + chunk_size])

    with Pool(processes=num_workers) as pool:
        results = pool.map(process_chunk, [(chunk,) for chunk in chunks])

    transliterated_keys = [key for sublist in results for key in sublist]

    transliterated_dict = {k: data[k] for k in transliterated_keys}
    cleaned_dict = {k: v for k, v in data.items() if k not in transliterated_keys}

    output_dir = input_path.parent
    transliterated_path = output_dir / "transliterated.json"
    cleaned_path = output_dir / "cleaned.json"

    with open(transliterated_path, "w", encoding="utf-8") as f:
        json.dump(transliterated_dict, f, ensure_ascii=False, indent=2)

    with open(cleaned_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_dict, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Found {len(transliterated_keys)} transliterated entries")
    print(f"📄 Transliterated: {transliterated_path}")
    print(f"📄 Cleaned: {cleaned_path}")
    print(f"📊 Original: {total}, Cleaned: {len(cleaned_dict)}, Removed: {len(transliterated_keys)}")


if __name__ == "__main__":
    main()
