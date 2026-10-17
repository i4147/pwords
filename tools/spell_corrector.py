from __future__ import annotations

import os
import pickle
import re
import string
from collections import Counter


class SpellCorrector:
    _NWORDS: Counter | None = None

    _ALPHABET = list(string.ascii_lowercase)

    _WORD_PATTERN = re.compile(r"[a-z]+")

    _DICT_PATH = "serialized_dictionary.pkl"
    _CORPUS_PATH = "/data/data/com.termux/files/home/nltk_data/corpora/words/en"

    @classmethod
    def _words(cls, text: str) -> list[str]:
        return cls._WORD_PATTERN.findall(text.lower())

    @classmethod
    def _train(cls, features: list[str]) -> Counter:
        return Counter(features)

    @classmethod
    def _edits1(cls, word: str) -> list[str]:
        n = len(word)
        edits: list[str] = []

        for i in range(n):
            edits.append(word[:i] + word[i + 1 :])
            for c in cls._ALPHABET:
                edits.append(word[:i] + c + word[i + 1 :])

        for i in range(n - 1):
            edits.append(word[:i] + word[i + 1] + word[i] + word[i + 2 :])

        for i in range(n + 1):
            for c in cls._ALPHABET:
                edits.append(word[:i] + c + word[i:])

        return edits

    @classmethod
    def _known_edits2(cls, word: str) -> list[str]:
        known: list[str] = []
        for e1 in cls._edits1(word):
            for e2 in cls._edits1(e1):
                if e2 in cls._NWORDS:
                    known.append(e2)
        return known

    @classmethod
    def _known(cls, words: list[str]) -> list[str]:
        return [w for w in words if w in cls._NWORDS]

    @classmethod
    def _load_dictionary(cls) -> None:
        if not os.path.exists(cls._DICT_PATH):
            with open(cls._CORPUS_PATH, encoding="utf-8") as f:
                text = f.read()
            cls._NWORDS = cls._train(cls._words(text))
            with open(cls._DICT_PATH, "wb") as f:
                pickle.dump(cls._NWORDS, f)
        else:
            with open(cls._DICT_PATH, "rb") as f:
                cls._NWORDS = pickle.load(f)

    @staticmethod
    def _is_numeric(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    @classmethod
    def correct(cls, word: str) -> str | None:
        word = word.strip()
        if not word:
            return None
        if cls._is_numeric(word):
            return word

        word = word.lower()

        if not cls._NWORDS:
            cls._load_dictionary()

        candidates: list[str] = []

        if cls._known([word]):
            return word

        if tmp_candidates := cls._known(cls._edits1(word)):
            candidates.extend(tmp_candidates)
        elif tmp_candidates := cls._known_edits2(word):
            candidates.extend(tmp_candidates)
        else:
            return word

        max_count = 0
        for c in candidates:
            value = cls._NWORDS[c]
            if value > max_count:
                max_count = value
                word = c

        return word


corrected = SpellCorrector.correct("speling")
print(corrected)
print(corrected)
