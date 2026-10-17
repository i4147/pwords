#!/usr/bin/env python3
"""
Script to detect and separate transliterated entries from Persian translations.
Identifies entries where the translation is just a phonetic spelling of the
English word rather than an actual translation.

Usage: python detect_transliteration.py <input.json>
Output: transliterated.json, cleaned.json
"""

import json
import sys
import re
from pathlib import Path
from multiprocessing import Pool
from typing import Tuple, Dict, Any


# Persian character sets
PERSIAN_LETTERS = set('الاأإآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئةؤ')
PERSIAN_DIACRITICS = set('ًٌٍَُِّْـ')
PERSIAN_CHARS = PERSIAN_LETTERS | PERSIAN_DIACRITICS | set('۰۱۲۳۴۵۶۷۸۹')


def is_persian_text(text: str) -> bool:
    """Check if text contains Persian characters."""
    if not text:
        return False
    persian_count = sum(1 for c in text if c in PERSIAN_CHARS)
    return persian_count > 0


def is_likely_transliteration(english_word: str, persian_translation: str) -> bool:
    """
    Detect if the Persian translation is likely just a transliteration
    of the English word rather than an actual translation.
    
    Returns: True if it's likely a transliteration (should be filtered out)
    """
    
    # Skip entries that don't contain Persian characters
    if not is_persian_text(persian_translation):
        return False
    
    english_word_lower = english_word.lower().strip()
    persian_clean = persian_translation.strip()
    
    # Check if it's a known type that shouldn't be translated
    if should_skip_translation(english_word_lower):
        return False
    
    # Check for phonetic similarity patterns
    if is_phonetic_match(english_word_lower, persian_clean):
        return True
    
    # Check if Persian text is suspiciously similar in structure to English word
    if has_similar_length_pattern(english_word_lower, persian_clean):
        return True
    
    return False


def should_skip_translation(word: str) -> bool:
    """
    Check if word is of a type that typically doesn't get translated.
    These are valid non-translations and should not be filtered out.
    """
    
    # Programming/technical abbreviations (lowercase, short)
    tech_terms = {'xor', 'regex', 'ioctl', 'stdio', 'stdin', 'stdout', 
                  'stderr', 'argv', 'argc', 'api', 'cpu', 'gpu', 'ram',
                  'url', 'uri', 'http', 'https', 'ftp', 'ssh', 'json',
                  'xml', 'sql', 'html', 'css', 'js', 'py', 'rb', 'go',
                  'rust', 'c++', 'java', 'php', 'node', 'npm', 'pip',
                  'git', 'svn', 'cvs', 'cli', 'gui', 'ui', 'ux', 'db'}
    if word in tech_terms:
        return True
    
    # Roman numerals (all lowercase sequences of i, v, x, l, c, d, m)
    if re.match(r'^[ivxlcdm]+$', word) and len(word) > 1:
        return True
    
    # All uppercase (likely abbreviations/acronyms)
    if word.isupper() and len(word) > 1:
        return True
    
    # Title case (likely proper nouns/brand names)
    if word and word[0].isupper() and len(word) > 2:
        return True
    
    # Common abbreviations pattern (ends with period or contains periods)
    if word.endswith('.') or word.count('.') > 0:
        return True
    
    # Known brand names and proper nouns
    brand_names = {
        'mongodb', 'github', 'verizon', 'google', 'amazon', 'microsoft',
        'apple', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
        'cowper', 'averroes', 'birdseye', 'xerox', 'kleenex'
    }
    if word.lower() in brand_names:
        return True
    
    return False


def is_phonetic_match(english_word: str, persian_text: str) -> bool:
    """
    Check if Persian text appears to be a phonetic transliteration.
    Looks for patterns where Persian letters are used to spell out English sounds.
    """
    
    # Common Persian transliteration patterns
    # These map English phonetics to Persian letters
    common_translit_patterns = {
        # English patterns -> Persian patterns
        r'(^|[^a-z])d(?=[aeiouy]|$)': ['د'],  # d sound
        r'(^|[^a-z])t(?=[aeiouy]|$)': ['ت'],  # t sound
        r'(^|[^a-z])s(?=[aeiouy]|$)': ['س'],  # s sound
        r'(^|[^a-z])z(?=[aeiouy]|$)': ['ز'],  # z sound
        r'(^|[^a-z])sh': ['ش'],  # sh sound
        r'(^|[^a-z])ch': ['چ'],  # ch sound
        r'(^|[^a-z])j': ['ج'],  # j sound
        r'(^|[^a-z])f': ['ف'],  # f sound
        r'(^|[^a-z])v': ['و'],  # v sound
        r'(^|[^a-z])k': ['ک'],  # k sound
        r'(^|[^a-z])g': ['گ'],  # g sound
        r'(^|[^a-z])l': ['ل'],  # l sound
        r'(^|[^a-z])m': ['م'],  # m sound
        r'(^|[^a-z])n': ['ن'],  # n sound
        r'(^|[^a-z])r': ['ر'],  # r sound
        r'(^|[^a-z])h': ['ه'],  # h sound
    }
    
    # If Persian text contains most of its characters in PERSIAN_LETTERS
    # and is roughly similar length to English word (±50%)
    if len(english_word) > 2 and len(persian_text) > 2:
        persian_letter_count = sum(1 for c in persian_text if c in PERSIAN_LETTERS)
        total_chars = len(persian_text)
        
        if total_chars > 0:
            letter_ratio = persian_letter_count / total_chars
            length_ratio = len(persian_text) / len(english_word)
            
            # High letter ratio suggests transliteration
            # Similar length suggests phonetic mapping
            if letter_ratio > 0.7 and 0.5 < length_ratio < 1.5:
                # Additional check: count potential phonetic matches
                matches = 0
                for pattern in common_translit_patterns:
                    if re.search(pattern, english_word):
                        matches += 1
                
                if matches >= 2:  # If multiple phonetic patterns match
                    return True
    
    return False


def has_similar_length_pattern(english_word: str, persian_text: str) -> bool:
    """
    Check if the structure/length relationship suggests transliteration.
    Transliterations typically preserve word length.
    """
    
    # Clean Persian text (remove diacritics)
    persian_clean = ''.join(c for c in persian_text if c not in PERSIAN_DIACRITICS)
    
    english_len = len(english_word)
    persian_len = len(persian_clean)
    
    # Transliterations usually have similar length (±30%)
    if english_len > 3:
        length_ratio = persian_len / english_len
        if 0.7 < length_ratio < 1.3:
            # Check if Persian text is mostly letters (not a real sentence)
            letter_ratio = sum(1 for c in persian_clean if c in PERSIAN_LETTERS) / len(persian_clean)
            if letter_ratio > 0.8:
                return True
    
    return False


def process_entry(item: Tuple[str, str]) -> Tuple[str, str, bool]:
    """
    Process a single dictionary entry.
    Returns: (english_word, persian_translation, is_transliteration)
    """
    english_word, persian_translation = item
    is_translit = is_likely_transliteration(english_word, persian_translation)
    return (english_word, persian_translation, is_translit)


def main():
    """Main function."""
    
    if len(sys.argv) < 2:
        print("Usage: python detect_transliteration.py <input.json>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Load JSON file
    print(f"Loading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    if not isinstance(data, dict):
        print("Error: JSON must be a dictionary")
        sys.exit(1)
    
    print(f"Total entries: {len(data)}")
    
    # Process entries with multiprocessing
    print("Processing entries with 8 workers...")
    with Pool(8) as pool:
        results = pool.map(process_entry, data.items())
    
    # Separate transliterated and cleaned entries
    transliterated = {}
    cleaned = {}
    
    for english_word, persian_translation, is_translit in results:
        if is_translit:
            transliterated[english_word] = persian_translation
        else:
            cleaned[english_word] = persian_translation
    
    # Save results
    output_dir = input_file.parent
    
    transliterated_file = output_dir / 'transliterated.json'
    cleaned_file = output_dir / 'cleaned.json'
    
    print(f"\nSaving results...")
    print(f"  Transliterated entries: {len(transliterated)}")
    print(f"  Cleaned entries: {len(cleaned)}")
    
    with open(transliterated_file, 'w', encoding='utf-8') as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved to {transliterated_file}")
    
    with open(cleaned_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved to {cleaned_file}")
    
    # Print some examples
    if transliterated:
        print(f"\nSample transliterated entries:")
        for i, (eng, per) in enumerate(list(transliterated.items())[:5]):
            print(f"  {eng:20} -> {per}")
    
    if cleaned:
        print(f"\nSample cleaned entries:")
        for i, (eng, per) in enumerate(list(cleaned.items())[:5]):
            print(f"  {eng:20} -> {per}")


if __name__ == '__main__':
    main()
