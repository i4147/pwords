import json
import re
from pathlib import Path

TAG_RE = re.compile(r"\s*\([^)]*\)\s*")

def main():
    path = Path.cwd() / "merged.json"
    if not path.exists():
        print(f"{path.name} not found.")
        return

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = {}
    for word, translations in data.items():
        if not isinstance(translations, list):
            translations = [translations]

        stripped = []
        for entry in translations:
            if not isinstance(entry, str):
                entry = str(entry)
            # remove all (...) groups, collapse extra spaces
            new_entry = TAG_RE.sub(" ", entry).strip()
            new_entry = re.sub(r"\s+", " ", new_entry)
            stripped.append(new_entry)

        cleaned[word] = stripped

    with path.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"Stripped tags from {len(cleaned)} words in {path.name}")


if __name__ == "__main__":
    main()