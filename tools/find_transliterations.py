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

    transliteration_digraphs = ["kh", "gh", "zh", "sh", "ch", "th", "dh", "q", "x", "w", "y"]
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
        with filepath.open("r", encoding="utf-8") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            content = mm.read().decode("utf-8")
            return json.loads(content)
    except FileNotFoundError:
        print(f"Error: Input file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file at {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading {filepath}: {e}", file=sys.stderr)
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
        print(f"Error: Input JSON file should contain a dictionary, but found {type(data)}.", file=sys.stderr)
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

    print(f"Saving {len(transliterated_entries)} transliterated entries to {output_transliterated_path}")
    with output_transliterated_path.open("w", encoding="utf-8") as f:
        json.dump(dict(transliterated_entries), f, ensure_ascii=False, indent=4)

    print(f"Saving {len(valid_entries)} valid entries to {output_cleaned_path}")
    with output_cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(valid_entries, f, ensure_ascii=False, indent=4)

    print("Processing complete.")


if __name__ == "__main__":
    main()

"""
1.  **`is_transliterated(persian_word, english_word)` Function:**
    *   This is the core logic for detecting transliterations.
    *   It uses several heuristics:
        *   **Basic Length Checks:** Very short English words are less likely to be meaningful translations.
        *   **Phonetic Mapping (Heuristic 3):** It attempts to map Persian characters to common phonetic English equivalents and checks if the resulting phonetic string is very similar to the English translation. This is a strong indicator.
        *   **Transliteration Markers (Heuristic 2):** It checks for common digraphs or letter combinations often used in transliteration (e.g., `kh`, `gh`, `sh`, `aa`, `oo`).
        *   **Common English Words (Heuristic 4):** If the English "translation" is a very common English word (like "the," "is," "book," "happy"), it's less likely to be a transliteration of a Persian word that *sounds* like that English word. This helps avoid falsely flagging translations that happen to sound similar.
    *   **Important:** Detecting transliteration accurately is challenging. This function uses heuristics that should work for many common cases, but it might not be perfect. You might need to tweak the heuristics based on your specific data.

2.  **`read_json_with_mmap(filepath)`:**
    *   Uses `pathlib` for path manipulation.
    *   Opens the file in binary read mode (`"r"` with `encoding="utf-8"`).
    *   Uses `mmap.mmap` to create a memory-mapped file. This allows you to treat the file's content as if it were in memory, potentially speeding up access for large files without loading the entire file at once.
    *   Decodes the memory-mapped bytes to a UTF-8 string.
    *   Parses the string into a Python dictionary using `json.loads()`.
    *   Includes error handling for file not found, JSON decoding errors, and other exceptions.

3.  **`process_entry(item)`:**
    *   A helper function that takes a single `(persian_word, english_translation)` tuple.
    *   Calls `is_transliterated` to determine the type.
    *   Returns a tuple indicating the type ("transliterated" or "valid") and the original item.

4.  **`worker_task(chunk)`:**
    *   This function is executed by each worker process.
    *   It receives a `chunk` (a list of dictionary items).
    *   It iterates through the chunk, calls `process_entry` for each item, and collects the results.

5.  **`main()` Function:**
    *   Parses command-line arguments using `sys.argv` and `pathlib`.
    *   Defines output file paths.
    *   Calls `read_json_with_mmap` to load the input data.
    *   Converts the dictionary `data.items()` into a list (`items_list`) so it can be easily divided into chunks.
    *   **Parallel Processing:**
        *   Calculates `chunk_size` to distribute the work evenly among `num_workers` (set to 8).
        *   Creates `chunks` by slicing `items_list`.
        *   Initializes `mp.Pool` with the specified number of worker processes.
        *   Uses `pool.map(worker_task, chunks)`: This is the core of the parallel execution. It distributes the `chunks` to the `worker_task` function across the 8 processes and collects all results.
    *   **Result Aggregation:**
        *   The `results_from_chunks` is a list of lists. It's flattened into `all_results`.
        *   It then iterates through `all_results` to separate `transliterated_entries` and rebuild the `valid_entries` dictionary.
    *   **Saving Output:**
        *   Saves the `transliterated_entries` to `transliterated.json`.
        *   Saves the remaining `valid_entries` to `cleaned.json`.
        *   Uses `ensure_ascii=False` to correctly handle Persian characters in the output JSON and `indent=4` for readability.

This script provides a solid framework for your task, balancing performance with the complexity of natural language processing. Remember that the accuracy of transliteration detection will depend heavily on the quality and sophistication of the `is_transliterated` function's heuristics.
"""
