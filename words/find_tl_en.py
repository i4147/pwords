#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

PERSIAN_CHARS = set("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیءآاًهٔة")
PERSIAN_SPECIFIC = set("پچژگکی")
ARABIC_SPECIFIC = set("ثحصضطظعق")
PERSIAN_COMMON_WORDS = {
    "و",
    "در",
    "به",
    "از",
    "که",
    "این",
    "را",
    "با",
    "برای",
    "تا",
    "بر",
    "هر",
    "هم",
    "نیز",
    "خود",
    "شد",
    "است",
    "بود",
    "کرد",
    "گفت",
    "دارد",
    "باشد",
    "نیست",
    "می",
    "های",
    "ها",
    "ان",
    "یک",
    "دو",
    "سه",
    "چه",
    "چرا",
    "کجا",
    "چگونه",
    "وقتی",
    "زمانی",
    "اگر",
    "اما",
    "یا",
    "نه",
    "بله",
    "خیر",
    "شاید",
    "حتماً",
    "البته",
    "مثلاً",
    "یعنی",
    "مانند",
    "قبل",
    "بعد",
    "حال",
    "آینده",
    "گذشته",
    "امروز",
    "دیروز",
    "فردا",
}
PERSIAN_AFFIXES = {
    "می",
    "نمی",
    "بی",
    "با",
    "هم",
    "نا",
    "پر",
    "کم",
    "خوش",
    "بد",
    "گر",
    "مند",
    "انه",
    "ها",
    "های",
    "ترین",
    "تر",
    "ام",
    "ات",
    "اش",
}


def is_roman_numeral(word):
    roman_pattern = re.compile(r"^[ivxlcdmIVXLCDM]+$")
    return bool(roman_pattern.match(word))


def is_technical_abbreviation(word):
    tech_abbrevs = {
        "xor",
        "regex",
        "ioctl",
        "stdio",
        "stdlib",
        "malloc",
        "http",
        "https",
        "ftp",
        "ssh",
        "tcp",
        "udp",
        "ip",
        "dns",
        "html",
        "css",
        "js",
        "json",
        "xml",
        "api",
        "cli",
        "gui",
        "ide",
        "sdk",
        "jdbc",
        "odbc",
        "sql",
        "nosql",
        "php",
        "asp",
        "jsp",
        "ajax",
        "rest",
        "soap",
        "wsdl",
    }
    return word.lower() in tech_abbrevs


def is_brand_name(word):
    brands = {
        "mongodb",
        "github",
        "verizon",
        "microsoft",
        "apple",
        "google",
        "amazon",
        "facebook",
        "twitter",
        "instagram",
        "whatsapp",
        "telegram",
        "linkedin",
        "netflix",
        "spotify",
        "dropbox",
        "slack",
        "zoom",
        "skype",
        "adobe",
        "oracle",
        "sap",
        "salesforce",
        "shopify",
        "wordpress",
        "drupal",
        "joomla",
        "magento",
        "prestashop",
    }
    return word.lower() in brands


def has_persian_meaning(text):
    persian_specific_count = sum(1 for char in text if char in PERSIAN_SPECIFIC)
    words = text.split()
    common_word_count = sum(1 for word in words if word in PERSIAN_COMMON_WORDS)
    has_affix = any(affix in text for affix in PERSIAN_AFFIXES)
    score = persian_specific_count * 2 + common_word_count * 3 + (2 if has_affix else 0)
    if len(words) > 1:
        score += 2
    return score >= 3


def is_transliteration(english_word, persian_text):
    if is_roman_numeral(english_word):
        return False
    if is_technical_abbreviation(english_word):
        return False
    if is_brand_name(english_word):
        return False
    eng_normalized = english_word.lower().strip()
    persian_normalized = persian_text.strip()
    if len(persian_normalized) < 2:
        return False
    if has_persian_meaning(persian_normalized):
        return False
    translit_indicators = []
    if eng_normalized.endswith("er") and persian_normalized.endswith("ر"):
        translit_indicators.append("er_sound")
    if "tion" in eng_normalized and "شن" in persian_normalized:
        translit_indicators.append("tion_sound")
    if "ph" in eng_normalized and "ف" in persian_normalized:
        translit_indicators.append("ph_sound")
    if "th" in eng_normalized and (
        "ت" in persian_normalized or "ث" in persian_normalized
    ):
        translit_indicators.append("th_sound")
    eng_letters = len([c for c in eng_normalized if c.isalpha()])
    persian_letters = len([c for c in persian_normalized if c in PERSIAN_CHARS])
    if abs(eng_letters - persian_letters) <= 2:
        translit_indicators.append("length_similarity")
    if not any(c in PERSIAN_SPECIFIC for c in persian_normalized):
        translit_indicators.append("no_persian_specific_chars")
    eng_vowels = re.findall(r"[aeiou]+", eng_normalized)
    persian_vowels = re.findall(r"[اوی]", persian_normalized)
    if (
        len(eng_vowels) > 0
        and len(persian_vowels) > 0
        and abs(len(eng_vowels) - len(persian_vowels)) <= 1
    ):
        translit_indicators.append("vowel_pattern")
    consonant_map = {
        "k": "ک",
        "g": "گ",
        "d": "د",
        "b": "ب",
        "p": "پ",
        "t": "ت",
        "s": "س",
        "m": "م",
        "n": "ن",
        "r": "ر",
        "l": "ل",
        "f": "ف",
        "v": "و",
        "z": "ز",
        "h": "ه",
    }
    mapped_consonants = 0
    total_consonants = 0
    for eng_char, persian_char in consonant_map.items():
        eng_count = eng_normalized.count(eng_char)
        if eng_count > 0:
            total_consonants += eng_count
            if persian_char in persian_normalized:
                mapped_consonants += 1
    if total_consonants > 0 and mapped_consonants / total_consonants > 0.5:
        translit_indicators.append("consonant_mapping")
    return len(translit_indicators) >= 2


def process_chunk(chunk):
    transliterated = {}
    cleaned = {}
    for eng_word, persian_translation in chunk:
        try:
            if is_transliteration(eng_word, persian_translation):
                transliterated[eng_word] = persian_translation
            else:
                cleaned[eng_word] = persian_translation
        except Exception as e:
            cleaned[eng_word] = persian_translation
    return transliterated, cleaned


def parallel_process(data_dict, num_workers=8):
    items = list(data_dict.items())
    chunk_size = max(1, len(items) // (num_workers * 4))
    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_chunk, chunks)
    transliterated = {}
    cleaned = {}
    for trans_dict, clean_dict in results:
        transliterated.update(trans_dict)
        cleaned.update(clean_dict)
    return transliterated, cleaned


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input.json>")
        sys.exit(1)
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    print(f"Loading JSON file: {input_file}")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    print(f"Total entries: {len(data)}")
    print("Processing with 8 parallel workers...")
    transliterated, cleaned = parallel_process(data, num_workers=8)
    output_dir = input_file.parent
    transliterated_file = output_dir / "1.transliterated.json"
    cleaned_file = output_dir / "2.cleaned.json"
    print(f"\nSaving transliterated entries to: {transliterated_file}")
    with open(transliterated_file, "w", encoding="utf-8") as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"Saving cleaned entries to: {cleaned_file}")
    with open(cleaned_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"\n{'=' * 40}")
    print(f"RESULTS:")
    print(f"{'=' * 40}")
    print(f"Total entries processed: {len(data)}")
    print(
        f"Transliterated entries: {len(transliterated)} ({len(transliterated) / len(data) * 40:.1f}%)"
    )
    print(f"Cleaned entries: {len(cleaned)} ({len(cleaned) / len(data) * 40:.1f}%)")
    print(f"{'=' * 40}")
    if transliterated:
        print("\nExample transliterated entries:")
        for _i, (eng, trans) in enumerate(list(transliterated.items())[:10]):
            print(f"  {eng} -> {trans}")
    if cleaned:
        print("\nExample cleaned entries:")
        for _i, (eng, trans) in enumerate(list(cleaned.items())[:10]):
            print(f"  {eng} -> {trans}")


if __name__ == "__main__":
    main()
