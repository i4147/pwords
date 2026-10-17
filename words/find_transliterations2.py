#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import mmap
import multiprocessing as mp
import re
import sys
from pathlib import Path


def is_transliterated(persian_word: str, english_word: str) -> bool:
    persian_word_lower = persian_word.lower()
    english_word_lower = english_word.lower()
    if len(english_word_lower) < 3:
        return False
    if not persian_word_lower:
        return False
    simplified_persian = re.sub(r"[آأ]", "a", persian_word_lower)
    simplified_persian = re.sub(r"[اوو]", "o", simplified_persian)
    simplified_persian = re.sub(r"[ایئ]", "i", simplified_persian)
    simplified_persian = re.sub(r"[eé]", "e", simplified_persian)
    simplified_persian = re.sub(r"[ \-\']", "", simplified_persian)
    english_alphanum = re.sub(r"[^a-z0-9]", "", english_word_lower)
    transliteration_digraphs = [
        "kh",
        "gh",
        "zh",
        "sh",
        "ch",
        "th",
        "dh",
        "q",
        "x",
        "w",
        "y",
    ]
    transliteration_vowels = ["a", "e", "i", "o", "u"]
    english_score = 0
    for char in english_word_lower:
        if char in transliteration_vowels:
            english_score += 0.5
        elif char.isalpha() and char not in "aeiou":
            english_score += 1
        else:
            english_score += 0.2
    if re.search(r"(aa|oo|ee|gh|kh|zh|sh|ch|q|x|w|y)", english_word_lower):
        return True
    persian_to_phonetic = {
        "ا": "a",
        "آ": "aa",
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
        "و": ["v", "o", "u"],
        "ه": "h",
        "ی": ["i", "e"],
        " ": "",
    }
    phonetic_persian = ""
    for char in persian_word:
        phonetic_persian += persian_to_phonetic.get(char, char)
    phonetic_persian_cleaned = re.sub(r"[^a-z]", "", phonetic_persian.lower())
    english_word_cleaned = re.sub(r"[^a-z]", "", english_word_lower)
    if len(phonetic_persian_cleaned) > 0 and len(english_word_cleaned) > 0:
        set1 = set(phonetic_persian_cleaned)
        set2 = set(english_word_cleaned)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        if union > 0 and intersection / union > 0.7:
            return True
    common_english_words = {
        "the",
        "a",
        "an",
        "is",
        "of",
        "to",
        "and",
        "in",
        "that",
        "it",
        "for",
        "on",
        "with",
        "as",
        "was",
        "be",
        "his",
        "he",
        "her",
        "she",
        "it's",
        "they",
        "I",
        "you",
        "we",
        "are",
        "this",
        "have",
        "from",
        "or",
        "by",
        "not",
        "but",
        "what",
        "when",
        "where",
        "who",
        "how",
        "all",
        "any",
        "no",
        "so",
        "too",
        "very",
        "good",
        "great",
        "bad",
        "new",
        "old",
        "big",
        "small",
        "like",
        "love",
        "hate",
        "see",
        "look",
        "go",
        "come",
        "make",
        "get",
        "take",
        "give",
        "do",
        "say",
        "tell",
        "ask",
        "work",
        "play",
        "run",
        "walk",
        "eat",
        "drink",
        "sleep",
        "house",
        "home",
        "car",
        "day",
        "night",
        "time",
        "year",
        "man",
        "woman",
        "child",
        "people",
        "world",
        "life",
        "thing",
        "hand",
        "eye",
        "head",
        "face",
        "book",
        "water",
        "food",
        "sun",
        "moon",
        "star",
        "sky",
        "ground",
        "tree",
        "flower",
        "animal",
        "bird",
        "fish",
        "dog",
        "cat",
        "horse",
        "city",
        "country",
        "language",
        "word",
        "name",
        "number",
        "color",
        "red",
        "blue",
        "green",
        "yellow",
        "white",
        "black",
        "hot",
        "cold",
        "happy",
        "sad",
        "long",
        "short",
        "tall",
        "fat",
        "thin",
        "young",
    }
    if english_word_lower in common_english_words:
        return False
    return False


def process_entry(item):
    persian_word, english_translation = item
    if is_transliterated(persian_word, english_translation):
        return "transliterated", item
    else:
        return "valid", item


def worker_task(chunk):
    results = []
    for item in chunk:
        results.append(process_entry(item))
    return results


def read_json_with_mmap(filepath: Path):
    try:
        with (
            filepath.open("r", encoding="utf-8") as f,
            mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm,
        ):
            content = mm.read().decode("utf-8")
            return json.loads(content)
    except FileNotFoundError:
        print(f"Error: Input file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file at {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(
            f"An unexpected error occurred while reading {filepath}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <input_json_file>")
        sys.exit(1)
    input_file_path = Path(sys.argv[1])
    output_transliterated_path = Path("transliterated.json")
    output_cleaned_path = Path("cleaned.json")
    print(f"Reading input file: {input_file_path}")
    data = read_json_with_mmap(input_file_path)
    if not isinstance(data, dict):
        print(
            f"Error: Input JSON file should contain a dictionary, but found {type(data)}.",
            file=sys.stderr,
        )
        sys.exit(1)
    items_list = list(data.items())
    num_items = len(items_list)
    num_workers = 8
    chunk_size = (num_items + num_workers - 1) // num_workers
    print(f"Processing {num_items} entries with {num_workers} workers...")
    chunks = [items_list[i : i + chunk_size] for i in range(0, num_items, chunk_size)]
    transliterated_entries = []
    valid_entries = {}
    with mp.Pool(processes=num_workers) as pool:
        results_from_chunks = pool.map(worker_task, chunks)
    all_results = [item for sublist in results_from_chunks for item in sublist]
    for entry_type, item in all_results:
        if entry_type == "transliterated":
            transliterated_entries.append(item)
        else:
            valid_entries[item[0]] = item[1]
    print(
        f"Saving {len(transliterated_entries)} transliterated entries to {output_transliterated_path}"
    )
    with output_transliterated_path.open("w", encoding="utf-8") as f:
        json.dump(dict(transliterated_entries), f, ensure_ascii=False, indent=4)
    print(f"Saving {len(valid_entries)} valid entries to {output_cleaned_path}")
    with output_cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(valid_entries, f, ensure_ascii=False, indent=4)
    print("Processing complete.")


if __name__ == "__main__":
    main()
