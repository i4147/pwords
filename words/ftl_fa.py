#!/usr/bin/env python3
from __future__ import annotations

import json
import mmap
import multiprocessing as mp
import re
import sys
import unicodedata
from pathlib import Path

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
    "ك": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "و": "v",
    "ه": "h",
    "ی": "y",
    "ی": "y",
    "ء": "",
    "ؤ": "u",
    "ئ": "y",
    "ۀ": "e",
    "ة": "e",
    "‌": "",
    "ً": "",
    "ٌ": "",
    "ٍ": "",
    "َ": "",
    "ُ": "",
    "ِ": "",
    "ْ": "",
    "ٓ": "",
    "ٰ": "",
}

VOWEL_MARKS = set("aeiouy")
LATIN_KEEP = re.compile(r"[a-z]+")

COMMON_TECH = {
    "api",
    "ip",
    "ui",
    "id",
    "usb",
    "json",
    "xml",
    "html",
    "css",
    "sql",
    "cpu",
    "ram",
    "api",
    "sdk",
    "http",
    "https",
    "tcp",
    "udp",
    "git",
    "dns",
}
COMMON_ABBREV_RE = re.compile(r"^[A-Z0-9][A-Z0-9\-.]{1,}$")


def normalize_fa(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("ی", "ی").replace("ك", "ک").replace("ۀ", "ه")
    s = re.sub(r"[\u064b-\u065f\u0670\u06d6-\u06ed]", "", s)
    s = s.replace("‌", "")
    return s.strip()


def normalize_en(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = s.replace("’", "'").replace("ʼ", "").replace("ʿ", "").replace("ʾ", "")
    s = re.sub(r"[^a-z]+", "", s)
    return s


def persian_to_ascii(word: str) -> str:
    out = []
    for ch in normalize_fa(word):
        out.append(PERSIAN_TO_LATIN.get(ch, ""))
    s = "".join(out)
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def simplify(s: str) -> str:
    s = normalize_en(s)
    s = s.replace("ph", "f").replace("kh", "x").replace("gh", "g")
    s = s.replace("ch", "c").replace("sh", "x").replace("zh", "j")
    s = s.replace("qu", "k").replace("ck", "k").replace("x", "sh")
    s = re.sub(r"[aeiouy]", "", s)
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def is_likely_transliteration(item):
    p, e = item
    if not isinstance(p, str) or not isinstance(e, str):
        return False, item
    p0, e0 = normalize_fa(p), e.strip()
    if not p0 or not e0:
        return False, item
    en = normalize_en(e0)
    if not en:
        return False, item

    if COMMON_ABBREV_RE.match(e0) or en in COMMON_TECH:
        return False, item

    if len(en) <= 2 and len(p0) > 2:
        return False, item

    target = persian_to_ascii(p0)
    sp, se = simplify(target), simplify(en)
    if not sp or not se:
        return False, item

    if sp == se:
        return True, item

    ratio = 0
    try:
        import difflib

        ratio = difflib.SequenceMatcher(None, sp, se).ratio()
    except Exception:
        ratio = 0

    common = len(set(sp) & set(se))
    vowel_ok = abs(sum(c in VOWEL_MARKS for c in target) - sum(c in VOWEL_MARKS for c in en)) <= 2

    likely = ratio >= 0.78 and common >= max(2, min(len(sp), len(se)) // 2) and vowel_ok
    if likely:
        return True, item

    if len(se) <= 4 and len(sp) <= 5 and ratio >= 0.72:
        return True, item

    return False, item


def load_input(path: Path):
    with path.open("rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            data = mm.read().decode("utf-8")
    return json.loads(data)


def main():
    inp = Path(sys.argv[1])
    data = load_input(inp)

    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = list(enumerate(data))
    else:
        raise ValueError("Input JSON must be an object or a list.")

    with mp.Pool(processes=8) as pool:
        results = pool.map(is_likely_transliteration, items)

    transliterated = {}
    cleaned = {}

    for flag, item in results:
        k, v = item
        if flag:
            transliterated[k] = v
        else:
            cleaned[k] = v

    out_dir = inp.parent
    (out_dir / "transliterated.json").write_text(
        json.dumps(transliterated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "cleaned.json").write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
