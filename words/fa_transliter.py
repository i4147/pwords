#!/usr/bin/env python3
"""
Script to detect and separate transliterated entries from English translations.
Identifies entries where the English translation is just a phonetic spelling of the
Persian word rather than an actual translation.

Usage: python detect_transliteration.py <input.json>
Output: transliterated.json, cleaned.json

Features:
- Uses mmap for efficient reading of large JSON files
- Parallel processing with 8 workers for fast detection
- Normalizes Persian text in cleaned output
- Handles proper nouns, brand names, and abbreviations
"""

import json
import sys
import re
import mmap
import unicodedata
from pathlib import Path
from multiprocessing import Pool
from typing import Tuple, Dict, Any, List


# Persian character sets
PERSIAN_LETTERS = set('الاأإآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئةؤ')
PERSIAN_DIACRITICS = set('ًٌٍَُِّْـ')
PERSIAN_CHARS = PERSIAN_LETTERS | PERSIAN_DIACRITICS | set('۰۱۲۳۴۵۶۷۸۹،؛؟')

# English vowels and consonants for pattern matching
ENGLISH_VOWELS = set('aeiouwy')
ENGLISH_CONSONANTS = set('bcdfghjklmnpqrstvxz')


def normalize_persian(text: str) -> str:
    """
    Normalize Persian text by removing diacritics and normalizing forms.
    """
    if not text:
        return text
    
    # NFD normalization to separate characters from diacritics
    text = unicodedata.normalize('NFD', text)
    # Remove all Persian diacritics
    text = ''.join(c for c in text if c not in PERSIAN_DIACRITICS)
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    return text.strip()


def is_persian_text(text: str) -> bool:
    """Check if text contains significant Persian characters."""
    if not text:
        return False
    persian_count = sum(1 for c in text if c in PERSIAN_CHARS)
    return persian_count > 0


def is_english_text(text: str) -> bool:
    """Check if text is predominantly English."""
    if not text:
        return False
    english_chars = sum(1 for c in text.lower() if c in 'abcdefghijklmnopqrstuvwxyz0123456789')
    return english_chars / len(text) > 0.6


def is_likely_transliteration(persian_word: str, english_translation: str) -> bool:
    """
    Detect if the English translation is likely just a transliteration
    of the Persian word rather than an actual translation.
    
    Returns: True if it's likely a transliteration (should be filtered out)
    """
    
    # Skip if English doesn't look like transliteration attempt
    if not is_english_text(english_translation):
        return False
    
    # Skip if translation is very short (likely valid)
    if len(english_translation.strip()) < 2:
        return False
    
    persian_normalized = normalize_persian(persian_word).lower()
    english_lower = english_translation.lower().strip()
    
    # Check if it's a known type that shouldn't be translated
    if should_skip_translation(persian_word, english_lower):
        return False
    
    # Check for phonetic similarity patterns
    if is_phonetic_match(persian_normalized, english_lower):
        return True
    
    # Check if English text is suspiciously similar in structure to Persian word
    if has_similar_length_pattern(persian_normalized, english_lower):
        return True
    
    # Check for common transliteration patterns
    if matches_transliteration_patterns(persian_normalized, english_lower):
        return True
    
    return False


def should_skip_translation(persian_word: str, english_text: str) -> bool:
    """
    Check if word is of a type that typically doesn't get translated.
    These are valid non-translations and should not be filtered out.
    """
    
    persian_normalized = normalize_persian(persian_word).lower()
    
    # Programming/technical abbreviations (lowercase, short, often with numbers)
    tech_terms = {
        'xor', 'regex', 'ioctl', 'stdio', 'stdin', 'stdout', 'stderr',
        'argv', 'argc', 'api', 'cpu', 'gpu', 'ram', 'url', 'uri', 'http',
        'https', 'ftp', 'ssh', 'json', 'xml', 'sql', 'html', 'css', 'js',
        'py', 'rb', 'go', 'rust', 'c++', 'java', 'php', 'node', 'npm',
        'pip', 'git', 'svn', 'cvs', 'cli', 'gui', 'ui', 'ux', 'db',
        'ai', 'ml', 'dl', 'cv', 'nlp', 'iot', 'bug', 'fix', 'cache'
    }
    if english_text in tech_terms:
        return True
    
    # All uppercase or mixed case with numbers (likely acronyms/brands)
    if len(english_text) > 1 and (english_text.isupper() or re.match(r'^[A-Z][a-zA-Z0-9]*$', english_text)):
        return True
    
    # Contains numbers (likely technical/model numbers)
    if any(c.isdigit() for c in english_text):
        return True
    
    # Common brand names and proper nouns (case-insensitive)
    brand_names = {
        'mongodb', 'github', 'verizon', 'google', 'amazon', 'microsoft',
        'apple', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
        'docker', 'kubernetes', 'linux', 'windows', 'macos',
        'cowper', 'averroes', 'birdseye', 'xerox', 'kleenex',
        'tesla', 'honda', 'toyota', 'ford', 'bmw', 'mercedes',
        'paris', 'london', 'berlin', 'tokyo', 'newyork', 'chicago',
        'john', 'james', 'william', 'david', 'robert', 'michael',
        'mary', 'sarah', 'emma', 'susan', 'jessica', 'linda'
    }
    if english_text.lower() in brand_names:
        return True
    
    # Starts with uppercase (likely proper noun)
    if english_text and english_text[0].isupper() and len(english_text) > 2:
        return True
    
    # Contains hyphens (often compound proper nouns)
    if '-' in english_text:
        return True
    
    # Known abbreviations pattern
    abbreviations = {
        'mr', 'mrs', 'dr', 'jr', 'sr', 'mgr', 'comdr', 'pvt', 'sgt',
        'etc', 'vs', 'eg', 'ie', 'am', 'pm', 'inc', 'ltd', 'co', 'corp'
    }
    if english_text.lower().rstrip('.') in abbreviations:
        return True
    
    return False


def matches_transliteration_patterns(persian_word: str, english_text: str) -> bool:
    """
    Check if the English text matches common Persian-to-English transliteration patterns.
    """
    
    # Common Persian letters and their typical transliteration patterns
    persian_to_english_patterns = {
        'ا': ['aa', 'a', 'ah'],
        'ب': ['b', 'be'],
        'پ': ['p', 'pe'],
        'ت': ['t', 'te', 'ta'],
        'ث': ['th', 'se'],
        'ج': ['j', 'ch', 'je'],
        'چ': ['ch', 'ch'],
        'ح': ['h', 'ha'],
        'خ': ['kh', 'kh'],
        'د': ['d', 'da'],
        'ذ': ['z', 'dh'],
        'ر': ['r', 'ra'],
        'ز': ['z', 'za'],
        'ژ': ['zh', 'zh'],
        'س': ['s', 'se'],
        'ش': ['sh', 'sh'],
        'ص': ['s', 'sad'],
        'ض': ['z', 'dad'],
        'ط': ['t', 'ta'],
        'ظ': ['z', 'za'],
        'ع': ['a', 'e', 'ain'],
        'غ': ['gh', 'gh'],
        'ف': ['f', 'fa'],
        'ق': ['q', 'gh', 'qa'],
        'ک': ['k', 'ka'],
        'گ': ['g', 'ga'],
        'ل': ['l', 'la'],
        'م': ['m', 'ma'],
        'ن': ['n', 'na'],
        'و': ['o', 'u', 'v', 'va'],
        'ه': ['h', 'e', 'ha'],
        'ی': ['y', 'i', 'e', 'ya'],
    }
    
    # Score how many Persian characters could transliterate to the English text
    if len(persian_word) > 2 and len(english_text) > 2:
        matching_chars = 0
        persian_letters = [c for c in persian_word if c in PERSIAN_LETTERS]
        
        for p_char in persian_letters:
            if p_char in persian_to_english_patterns:
                patterns = persian_to_english_patterns[p_char]
                # Check if any pattern appears in the English text
                for pattern in patterns:
                    if pattern in english_text:
                        matching_chars += 1
                        break
        
        # If more than 40% of Persian letters have matching patterns
        if len(persian_letters) > 0:
            match_ratio = matching_chars / len(persian_letters)
            if match_ratio > 0.4:
                return True
    
    return False


def is_phonetic_match(persian_word: str, english_text: str) -> bool:
    """
    Check if the English text appears to be a phonetic transliteration.
    """
    
    if len(persian_word) < 2 or len(english_text) < 2:
        return False
    
    # Length similarity check - transliterations preserve approximate length
    length_ratio = len(english_text) / len(persian_word)
    if 0.6 < length_ratio < 1.6:
        # Check if the structure suggests letter-by-letter transliteration
        # (most of the English text is made of letters, not numbers or symbols)
        letter_ratio = sum(1 for c in english_text if c.isalpha()) / len(english_text)
        if letter_ratio > 0.85:
            return True
    
    return False


def has_similar_length_pattern(persian_word: str, english_text: str) -> bool:
    """
    Check if the structure/length relationship suggests transliteration.
    Transliterations typically preserve word length.
    """
    
    if len(persian_word) < 3 or len(english_text) < 3:
        return False
    
    # Transliterations usually have 0.7-1.3x the length of original
    length_ratio = len(english_text) / len(persian_word)
    
    if 0.7 < length_ratio < 1.3:
        # Check if English text is mostly letters (not a real translation with spaces/punctuation)
        letter_ratio = sum(1 for c in english_text if c.isalpha()) / len(english_text)
        if letter_ratio > 0.9:
            return True
    
    return False


def process_entry(item: Tuple[str, str]) -> Tuple[str, str, bool]:
    """
    Process a single dictionary entry.
    Returns: (persian_word, english_translation, is_transliteration)
    """
    persian_word, english_translation = item
    is_translit = is_likely_transliteration(persian_word, english_translation)
    return (persian_word, english_translation, is_translit)


def load_json_with_mmap(file_path: Path) -> Dict[str, str]:
    """
    Load JSON file using mmap for efficient memory usage with large files.
    """
    with open(file_path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
            # Read the entire file into memory via mmap
            json_content = mmapped_file.read().decode('utf-8')
            data = json.loads(json_content)
    
    return data


def main():
    """Main function."""
    
    if len(sys.argv) < 2:
        print("Usage: python detect_transliteration.py <input.json>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Load JSON file using mmap
    print(f"Loading {input_file} with mmap...")
    try:
        data = load_json_with_mmap(input_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    if not isinstance(data, dict):
        print("Error: JSON must be a dictionary")
        sys.exit(1)
    
    print(f"Total entries: {len(data):,}")
    
    # Process entries with multiprocessing
    print("Processing entries with 8 workers...")
    with Pool(8) as pool:
        results = pool.map(process_entry, data.items())
    
    # Separate transliterated and cleaned entries
    transliterated = {}
    cleaned = {}
    
    for persian_word, english_translation, is_translit in results:
        if is_translit:
            transliterated[persian_word] = english_translation
        else:
            # Normalize Persian words in cleaned dictionary
            normalized_persian = normalize_persian(persian_word)
            cleaned[normalized_persian] = english_translation
    
    # Save results
    output_dir = input_file.parent
    
    transliterated_file = output_dir / 'transliterated.json'
    cleaned_file = output_dir / 'cleaned.json'
    
    print(f"\nSaving results...")
    print(f"  Transliterated entries: {len(transliterated):,}")
    print(f"  Cleaned entries: {len(cleaned):,}")
    print(f"  Removed: {len(transliterated):,} ({100*len(transliterated)/len(data):.1f}%)")
    
    # Save transliterated entries
    with open(transliterated_file, 'w', encoding='utf-8') as f:
        json.dump(transliterated, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved to {transliterated_file}")
    
    # Save cleaned entries (with normalized Persian words)
    with open(cleaned_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved to {cleaned_file}")
    
    # Print some examples of transliterated entries found
    if transliterated:
        print(f"\n📍 Sample TRANSLITERATED entries (removed):")
        for i, (per, eng) in enumerate(list(transliterated.items())[:10]):
            normalized = normalize_persian(per)
            print(f"  {i+1}. '{normalized}' -> '{eng}'")
    
    # Print some examples of cleaned entries
    if cleaned:
        print(f"\n✓ Sample CLEANED entries (kept, normalized):")
        for i, (per, eng) in enumerate(list(cleaned.items())[:10]):
            print(f"  {i+1}. '{per}' -> '{eng}'")


if __name__ == '__main__':
    main()
