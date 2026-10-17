import re
import sys
from pathlib import Path
import unicodedata
import json

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


if __name__ == "__main__":
    fn = sys.argv[1]
    with open(fn, encoding="utf-8") as f:
        data = json.load(f)
    cleaned = {}
    changed = {}
    for k, v in data.items():
        new_k = normalize_persian(k)
        if new_k != k:
            print(f"{k}  {new_k}")
            changed[new_k] = v
        else:
            cleaned[new_k] = v
    with open(fn, "w", encoding="utf-8") as fo:
        json.dump(cleaned, fo, ensure_ascii=False, indent=2)
    with open("changed.json", encoding="utf-8") as fc:
        json.dump(changed, fc, ensure_ascii=False, indent=2)
