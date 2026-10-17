#!/usr/bin/env python3
"""Detect transliterated entries in a bilingual fa-en / en-fa JSON dictionary.

Records look like  "الکترو": "Electro"  (fa-en)  or  "Electro": "الکترو"  (en-fa).
An entry is flagged when the Latin side is a plausible Finglish spelling of the
Persian side, using the tables and dictionaries shipped with the f2p and p2f
modules.

Usage:
    python find_transliterated.py dict.json          # report only
    python find_transliterated.py dict.json -m       # move hits to
                                                     # transliterated_faen.json (or _enfa.json),
                                                     # original file updated in place
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import re
import sys
import tempfile
from functools import lru_cache

# The f2p / p2f modules print progress messages on import; silence them.
with contextlib.redirect_stdout(io.StringIO()):
    p2f_mod = importlib.import_module("p2f.p2f")
    f2p_mod = importlib.import_module("f2p.f2p")

P_BEGIN, P_MIDDLE, P_END = p2f_mod.beginning, p2f_mod.middle, p2f_mod.ending
P2F_DICT = p2f_mod.dictionary  # persian -> "finglish1 finglish2 ..."
F2P_DICT = f2p_mod.dictionary  # finglish -> persian

PERSIAN_CHAR = re.compile(r"[\u0600-\u06FF]")
LATIN_CHAR = re.compile(r"[A-Za-z]")
SENSE_SPLIT = re.compile(r"\s*[;,،|]\s*")
EN_WORD_SPLIT = re.compile(r"[\s\-_/.:()]+")
VOWELS = set("aeiou")


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------
def norm_fa(s: str) -> str:
    s = s.replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه").replace("إ", "ا")
    return re.sub("[\u064b-\u065f\u0670\u0640\u200c\u200d\u200e\u200f]", "", s)


def canon(s: str) -> str:
    """Canonical lowercase latin form: ee->i, oo/ou->u, collapse doubled letters."""
    s = s.lower().replace("'", "")
    s = s.replace("ee", "i").replace("oo", "u").replace("ou", "u")
    return re.sub(r"(.)\1+", r"\1", s)


def en_variants(word: str) -> set[str]:
    """Spelling variants of an English word (c->k/s, ph->f, x->ks ...)."""
    w = re.sub(r"[^a-z']", "", word.lower())
    w = w.replace("ph", "f").replace("ck", "k").replace("x", "ks")
    w = w.replace("ch", "\x01").replace("sh", "\x02")
    parts = w.split("c")
    if len(parts) - 1 > 4:  # too many c's, just use k
        variants = {"k".join(parts)}
    else:
        variants = {""}
        for idx, part in enumerate(parts):
            if idx == 0:
                variants = {part}
            else:
                variants = {v + c + part for v in variants for c in ("k", "s")}
    return {canon(v.replace("\x01", "ch").replace("\x02", "sh")) for v in variants}


# --------------------------------------------------------------------------
# word level matching
# --------------------------------------------------------------------------
def dict_match(fa_raw: str, en: str) -> bool:
    en_l = en.lower()
    en_plain = re.sub(r"[^a-z']", "", en_l)
    cands = P2F_DICT.get(fa_raw, "").split()
    if en_l in cands or en_plain in cands:
        return True
    return F2P_DICT.get(en_l) == fa_raw or F2P_DICT.get(en_plain) == fa_raw


def table_match(fa: str, en_variants_set: set[str], strict: bool) -> bool:
    """Is there an alignment of the Persian letters to the latin string using
    the p2f tables?  Unless strict, unmatched latin short vowels may be skipped
    (Persian does not write them)."""
    n = len(fa)

    def options(i: int, k: int):
        tok = fa[i : i + k]
        table = P_BEGIN if i == 0 else (P_END if i + k == n else P_MIDDLE)
        opts = table.get(tok)
        if opts is None and k == 1:
            opts = P_MIDDLE.get(tok) or P_END.get(tok) or P_BEGIN.get(tok)
        return opts

    for e in en_variants_set:
        if not e:
            continue

        @lru_cache(maxsize=None)
        def go(i: int, j: int) -> bool:
            if i == n:
                return j == len(e) or (not strict and set(e[j:]) <= VOWELS)
            if not strict and j < len(e) and e[j] in VOWELS and go(i, j + 1):
                return True
            for k in (3, 2, 1):
                if i + k > n:
                    continue
                opts = options(i, k)
                if not opts:
                    continue
                for o in opts:
                    o = "" if o == "nothing" else canon(o)
                    if e.startswith(o, j) and (o or True) and go(i + k, j + len(o)):
                        return True
            return False

        if go(0, 0):
            return True
    return False


def word_match(fa_raw: str, en_raw: str, strict: bool) -> bool:
    fa = norm_fa(fa_raw)
    en_letters = re.sub(r"[^A-Za-z']", "", en_raw)
    if len(fa) < 2 or len(en_letters.replace("'", "")) < 2:
        return False
    if PERSIAN_CHAR.sub("", fa):  # digits, latin, punctuation inside the word
        return False
    if dict_match(fa_raw.strip(), en_raw.strip()):
        return True
    return table_match(fa, en_variants(en_letters), strict)


def phrase_match(fa: str, en: str, strict: bool) -> bool:
    fa_words = [w for w in fa.split() if w]
    en_words = [w for w in EN_WORD_SPLIT.split(en) if w]
    if not fa_words or not en_words:
        return False
    if len(fa_words) == len(en_words):
        return all(word_match(f, e, strict) for f, e in zip(fa_words, en_words))
    return word_match("".join(fa_words), "".join(en_words), strict)


def entry_match(fa: str, en: str, strict: bool) -> bool:
    fa_s = [s for s in SENSE_SPLIT.split(fa.strip()) if s]
    en_s = [s for s in SENSE_SPLIT.split(en.strip()) if s]
    if not fa_s or not en_s:
        return False
    if len(fa_s) == len(en_s):
        return all(phrase_match(f, e, strict) for f, e in zip(fa_s, en_s))
    if len(fa_s) == 1:
        return all(phrase_match(fa_s[0], e, strict) for e in en_s)
    return False


# --------------------------------------------------------------------------
# dictionary level
# --------------------------------------------------------------------------
def orientation(k: str, v: str):
    """Return 'faen', 'enfa' or None for a record."""
    kf, vf = bool(PERSIAN_CHAR.search(k)), bool(PERSIAN_CHAR.search(v))
    if kf and not vf and LATIN_CHAR.search(v):
        return "faen"
    if vf and not kf and LATIN_CHAR.search(k):
        return "enfa"
    return None


def find_transliterated(data: dict, strict: bool):
    found, kinds = {}, {"faen": 0, "enfa": 0}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        kind = orientation(k, v)
        if kind is None:
            continue
        kinds[kind] += 1
        fa, en = (k, v) if kind == "faen" else (v, k)
        if entry_match(fa, en, strict):
            found[k] = v
    direction = "faen" if kinds["faen"] >= kinds["enfa"] else "enfa"
    return found, direction


def write_json_atomic(path: str, obj) -> None:
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="bilingual fa-en or en-fa JSON dictionary")
    ap.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="move found entries to transliterated_<faen|enfa>.json "
        "(removed from the original file, which is updated in place)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="do not allow skipping unwritten short vowels (fewer hits, fewer false positives)",
    )
    ap.add_argument("-q", "--quiet", action="store_true", help="do not list every hit")
    args = ap.parse_args(argv)

    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        ap.error("top-level JSON value must be an object {word: translation}")

    found, direction = find_transliterated(data, args.strict)

    if not args.quiet:
        for k, v in found.items():
            print(f"{k}\t{v}")
    print(f"{len(found)} transliterated of {len(data)} entries ({direction})", file=sys.stderr)

    if args.move and found:
        out = os.path.join(os.path.dirname(os.path.abspath(args.file)), f"transliterated_{direction}.json")
        existing = {}
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                existing = json.load(f)
        existing.update(found)
        write_json_atomic(out, existing)  # write the new file first, then shrink the original
        write_json_atomic(args.file, {k: v for k, v in data.items() if k not in found})
        print(f"moved {len(found)} entries to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
