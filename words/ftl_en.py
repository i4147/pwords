#!/usr/bin/env python3
import json
import sys
import re
import multiprocessing as mp
from pathlib import Path

PERSIAN_RE = re.compile(r"^[\u0600-\u06FF\u0670-\u06D3\u200c\s\-\']+$")
LATIN_RE = re.compile(r"^[A-Za-z0-9]+(?:[A-Za-z0-9\-\']*[A-Za-z0-9]+)?$")
ROMAN_RE = re.compile(
    r"^(?=[mdclxvi]+$)m{0,4}(cm|cd|d?c{0,3})"
    r"(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$",
    re.I,
)

ROMAN_LIKE = {"i", "v", "x", "l", "c", "d", "m"}

# Very small transliteration expectations for Persian letters often used in phonetic spellings.
# This is intentionally permissive; it is used to detect "looks transliterated", not exact transliteration.
PERSIAN_EQUIV = {
    "a": {"ا", "آ", "ع"},
    "b": {"ب"},
    "c": {"ک", "س", "چ"},
    "d": {"د"},
    "e": {"e", "i", "ə"},
    "f": {"ف"},
    "g": {"گ", "ج"},
    "h": {"ه", "ح"},
    "i": {"ی", "ای"},
    "j": {"ج"},
    "k": {"ک", "ق"},
    "l": {"ل"},
    "m": {"م"},
    "n": {"ن"},
    "o": {"و", "ا"},
    "p": {"پ"},
    "q": {"ق", "ک"},
    "r": {"ر"},
    "s": {"س", "ص", "ث"},
    "t": {"ت", "ط"},
    "u": {"و", "او"},
    "v": {"و", "ف"},
    "w": {"و"},
    "x": {"خ", "کس"},
    "y": {"ی"},
    "z": {"ز", "ض", "ظ", "ذ"},
    "sh": {"ش"},
    "ch": {"چ"},
    "kh": {"خ"},
    "gh": {"غ", "ق"},
    "zh": {"ژ"},
    "oo": {"و"},
    "ee": {"ی"},
    "aa": {"ا", "آ"},
}

ABBREVIATIONS = {"mgr", "comdr", "pvt", "ioctl", "stdio", "xor", "regex"}


def normalize_fa(s: str) -> str:
    s = s.strip().lower()
    return re.sub(r"[\u064b-\u065f\u0670]", "", s)


def is_known_nontranslatable(en: str) -> bool:
    e = en.strip()
    el = e.lower()
    if el in ABBREVIATIONS:
        return True
    if ROMAN_RE.match(el):
        return True
    if len(e) <= 5 and e.isalpha() and e[:1].isupper() and e[1:].islower():
        return True
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9&._-]*", e) and any(ch.isdigit() for ch in e):
        return True
    if re.fullmatch(r"[A-Z]{2,}", e):
        return True
    return False


def looks_transliterated(en: str, fa: str) -> bool:
    e = en.strip()
    f = normalize_fa(fa)
    if not f or not PERSIAN_RE.match(f):
        return False
    if is_known_nontranslatable(e):
        return False

    el = e.lower().replace("-", "").replace("_", "")
    if len(el) <= 2:
        return False

    # Strong signal: Persian text is just the Persianized spelling of the Latin word.
    # We check if a large part of the Latin word can be represented by common Persian translit patterns.
    hit = 0
    i = 0
    while i < len(el):
        matched = False
        for n in (2, 1):
            part = el[i : i + n]
            if part in PERSIAN_EQUIV and any(x in f for x in PERSIAN_EQUIV[part]):
                hit += n
                i += n
                matched = True
                break
        if not matched:
            i += 1

    ratio = hit / max(1, len(el))
    if ratio >= 0.6:
        return True

    # Common phonetic spellings: English word copied into Persian script, often preserving sound more than meaning.
    compact = f.replace(" ", "")
    if len(compact) >= 3 and len(compact) <= len(el) + 3:
        if compact.startswith((
            "ای",
            "ا",
            "بی",
            "سی",
            "دی",
            "جی",
            "کی",
            "ال",
            "ام",
            "ان",
            "او",
            "پی",
            "تی",
            "وی",
            "زد",
        )):
            return True

    return False


def worker(item):
    en, fa = item
    return (en, fa) if looks_transliterated(en, fa) else None


def main():
    input_path = Path(sys.argv[1])
    data = json.loads(input_path.read_text(encoding="utf-8"))

    items = list(data.items())
    with mp.Pool(8) as pool:
        results = pool.map(worker, items)

    translit = {k: v for k, v in results if k is not None}
    cleaned = {k: v for k, v in items if k not in translit}

    Path("transliterated.json").write_text(
        json.dumps(translit, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    Path("cleaned.json").write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    mp.freeze_support()
    main()
