#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import mmap
import re
import sys
from multiprocessing import Pool
from pathlib import Path


class TransliterationDetector:
    def __init__(self):
        self.persian_to_english_map = {
            "ا": ["a", "ā", "â", "aa", "e"],
            "آ": ["a", "ā", "â", "aa"],
            "ب": ["b"],
            "پ": ["p"],
            "ت": ["t"],
            "ث": ["s", "th"],
            "ج": ["j"],
            "چ": ["ch", "č", "c"],
            "ح": ["h", "ḥ"],
            "خ": ["kh", "x"],
            "د": ["d"],
            "ذ": ["z", "th", "dh"],
            "ر": ["r"],
            "ز": ["z"],
            "ژ": ["zh", "ž", "j"],
            "س": ["s"],
            "ش": ["sh", "š"],
            "ص": ["s", "ṣ"],
            "ض": ["z", "ż", "ḍ"],
            "ط": ["t", "ṭ"],
            "ظ": ["z", "ẓ"],
            "ع": ["a", "e", "o", "'", "ʿ", "’"],
            "غ": ["gh", "q", "ğ"],
            "ف": ["f"],
            "ق": ["gh", "q", "ġ"],
            "ک": ["k"],
            "گ": ["g"],
            "ل": ["l"],
            "م": ["m"],
            "ن": ["n"],
            "و": ["v", "w", "u", "o", "ū", "ō"],
            "ه": ["h", "a", "e"],
            "ی": ["y", "i", "ī", "ē", "ey", "ei"],
            "ء": ["'", "’"],
            "ٔ": ["'", "’"],
            "ً": ["an", "un", "in"],
            "ٌ": ["un", "on"],
            "ٍ": ["in", "en"],
            "َ": ["a", "e"],
            "ُ": ["o", "u"],
            "ِ": ["e", "i"],
            "ّ": [""],
            "ْ": [""],
            "ـ": [""],
        }
        self.common_persian_words = {
            "آب": "water",
            "آتش": "fire",
            "آدم": "person",
            "آسمان": "sky",
            "آمدن": "to come",
            "آن": "that",
            "آنها": "they",
            "ابر": "cloud",
            "اسب": "horse",
            "اسم": "name",
            "امروز": "today",
            "امید": "hope",
            "این": "this",
            "با": "with",
            "باد": "wind",
            "باران": "rain",
            "باز": "open",
            "باید": "must",
            "بچه": "child",
            "بد": "bad",
            "بر": "on",
            "بزرگ": "big",
            "بعد": "after",
            "بله": "yes",
            "به": "to",
            "بیرون": "outside",
            "پدر": "father",
            "پر": "full",
            "پس": "then",
            "پنجره": "window",
            "تا": "until",
            "تازه": "fresh",
            "تمام": "complete",
            "تنها": "alone",
            "تو": "you",
            "جا": "place",
            "جوان": "young",
            "چرا": "why",
            "چشم": "eye",
            "چطور": "how",
            "چند": "how many",
            "چی": "what",
            "حالا": "now",
            "خدا": "god",
            "خراب": "broken",
            "خوب": "good",
            "خانه": "house",
            "خیلی": "very",
            "دست": "hand",
            "دل": "heart",
            "دو": "two",
            "دوست": "friend",
            "دیروز": "yesterday",
            "راه": "road",
            "روز": "day",
            "زبان": "language",
            "زندگی": "life",
            "زیبا": "beautiful",
            "سال": "year",
            "سر": "head",
            "سرد": "cold",
            "سفید": "white",
            "سلام": "hello",
            "شب": "night",
            "شما": "you",
            "شهر": "city",
            "صبح": "morning",
            "صد": "hundred",
            "کار": "work",
            "کتاب": "book",
            "کدام": "which",
            "کم": "little",
            "کوچک": "small",
            "گرم": "warm",
            "مادر": "mother",
            "ما": "we",
            "مرد": "man",
            "مردم": "people",
            "من": "I",
            "مهتاب": "moonlight",
            "نان": "bread",
            "نور": "light",
            "هیچ": "none",
            "هم": "also",
            "همه": "all",
            "هنوز": "still",
            "هوا": "air",
        }

    def persian_to_transliteration_pattern(self, persian_word: str) -> str:
        pattern_parts = []
        for char in persian_word:
            if char in self.persian_to_english_map:
                transliterations = self.persian_to_english_map[char]
                escaped = [re.escape(t) if t else "" for t in transliterations]
                escaped = [e for e in escaped if e]
                if escaped:
                    pattern_parts.append(f"({'|'.join(escaped)})")
            else:
                pattern_parts.append(".")
        return "".join(pattern_parts)

    def is_transliteration(self, persian_word: str, translation: str) -> bool:
        if not persian_word or not translation:
            return False
        if persian_word in self.common_persian_words:
            expected_meaning = self.common_persian_words[persian_word].lower()
            if expected_meaning == translation.lower().strip():
                return False
        persian_clean = persian_word.strip()
        translation_clean = translation.strip().lower()
        translation_clean = translation_clean.replace("ā", "a").replace("â", "a")
        translation_clean = translation_clean.replace("ī", "i").replace("ē", "e")
        translation_clean = translation_clean.replace("ū", "u").replace("ō", "o")
        translation_clean = translation_clean.replace("š", "sh").replace("č", "ch")
        translation_clean = translation_clean.replace("ž", "zh").replace("ğ", "gh")
        translation_clean = translation_clean.replace("ḥ", "h").replace("ṣ", "s")
        translation_clean = translation_clean.replace("ṭ", "t").replace("ẓ", "z")
        translation_clean = translation_clean.replace("ż", "z").replace("ḍ", "d")
        translation_clean = translation_clean.replace("ġ", "gh").replace("ʿ", "'")
        translation_clean = translation_clean.replace("’", "'")
        pattern = self.persian_to_transliteration_pattern(persian_clean)
        try:
            match = re.match(f"^{pattern}$", translation_clean, re.IGNORECASE)
            if match:
                return True
        except re.error:
            pass
        similarity = self.calculate_similarity(persian_clean, translation_clean)
        if similarity > 0.7:
            return True
        return self.looks_like_transliteration(persian_clean, translation_clean)

    def looks_like_transliteration(self, persian_word: str, translation: str) -> bool:
        transliteration_markers = [
            "kh",
            "gh",
            "ch",
            "sh",
            "zh",
            "aa",
            "ee",
            "oo",
            "'",
            "’",
            "-",
            "_",
        ]
        if len(translation) < 3 and len(persian_word) < 4:
            return True
        marker_count = sum(
            1 for marker in transliteration_markers if marker in translation
        )
        if marker_count >= 2:
            return True
        if translation.islower() and len(translation) > 3:
            common_english = {
                "the",
                "and",
                "for",
                "are",
                "but",
                "not",
                "you",
                "all",
                "can",
                "had",
                "her",
                "was",
                "one",
                "our",
                "out",
                "has",
                "his",
                "they",
                "she",
                "him",
                "them",
                "with",
                "from",
                "this",
                "that",
                "these",
                "those",
                "what",
                "where",
                "when",
            }
            if translation not in common_english:
                return True
        return False

    def calculate_similarity(self, persian_word: str, translation: str) -> float:
        expected = self.generate_transliteration(persian_word)
        if not expected:
            return 0.0
        return 1 - (
            self.levenshtein_distance(expected, translation)
            / max(len(expected), len(translation))
        )

    def generate_transliteration(self, persian_word: str) -> str:
        result = []
        for char in persian_word:
            if char in self.persian_to_english_map:
                transliterations = self.persian_to_english_map[char]
                if transliterations and transliterations[0]:
                    result.append(transliterations[0])
        return "".join(result)

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return TransliterationDetector.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]


def process_chunk(args: Tuple[str, str]) -> Tuple[str, str, bool]:
    persian_word, translation = args
    detector = TransliterationDetector()
    is_translit = detector.is_transliteration(persian_word, translation)
    return (persian_word, translation, is_translit)


def read_json_mmap(file_path: Path):
    with (
        open(file_path, "rb") as f,
        mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file,
    ):
        content = mmapped_file.read().decode("utf-8")
        return json.loads(content)


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input.json>")
        print("Example: python script.py out.json")
        sys.exit(1)
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File {input_path} does not exist")
        sys.exit(1)
    if input_path.suffix != ".json":
        print(f"Warning: File {input_path} does not have .json extension")
    print(f"Reading {input_path}...")
    print("Using mmap for fast reading...")
    try:
        data = read_json_mmap(input_path)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)
    if not isinstance(data, dict):
        print("Error: JSON file should contain a dictionary of word pairs")
        sys.exit(1)
    print(f"Loaded {len(data)} translation pairs")
    print("Detecting transliterations with parallel processing (8 workers)...")
    items = list(data.items())
    with Pool(processes=8) as pool:
        results = pool.map(process_chunk, items)
    transliterated = {}
    cleaned = {}
    for persian_word, translation, is_translit in results:
        if is_translit:
            transliterated[persian_word] = translation
        else:
            cleaned[persian_word] = translation
    output_dir = input_path.parent
    transliterated_path = output_dir / "transliterated.json"
    cleaned_path = output_dir / "cleaned.json"
    print("\nResults:")
    print(f"  Total pairs: {len(data)}")
    print(
        f"  Transliterated: {len(transliterated)} ({len(transliterated) / len(data) * 40:.1f}%)"
    )
    print(f"  Cleaned: {len(cleaned)} ({len(cleaned) / len(data) * 40:.1f}%)")
    with open(transliterated_path, "w", encoding="utf-8") as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved transliterated pairs to: {transliterated_path}")
    with open(cleaned_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved cleaned pairs to: {cleaned_path}")
    if transliterated:
        print("\nExample transliterated pairs (first 10):")
        for _i, (persian, trans) in enumerate(list(transliterated.items())[:10]):
            print(f"  {persian} -> {trans}")


if __name__ == "__main__":
    main()
