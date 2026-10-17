import json
import re
from pathlib import Path
from collections import defaultdict


def normalize_source(filename: str) -> str:
    """Turn 'essential-english-words-2' into 'essential-english-words' and strip trailing -N."""
    stem = Path(filename).stem
    # remove trailing -<digits>
    return re.sub(r"-\d+$", "", stem)


def main():
    current_dir = Path.cwd()
    merged = defaultdict(list)
    json_files = [f for f in current_dir.glob("*.json") if f.name != "merged.json"]

    if not json_files:
        print("No JSON files found to merge.")
        return

    for json_file in sorted(json_files):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skipping {json_file.name}: {e}")
            continue

        if not isinstance(data, dict):
            print(f"Skipping {json_file.name}: not a JSON object.")
            continue

        source = normalize_source(json_file.name)

        for word, translations in data.items():
            if not isinstance(translations, list):
                translations = [translations]
            for t in translations:
                if not isinstance(t, str):
                    t = str(t)
                # Avoid double-tagging if already present
                if f"({source})" in t:
                    tagged = t
                else:
                    tagged = f"{t} ({source})"

                if tagged not in merged[word]:
                    merged[word].append(tagged)

        print(f"Processed {json_file.name} -> source tag: ({source})")

    output_path = current_dir / "merged.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(dict(merged), f, ensure_ascii=False, indent=2)

    print(f"\nMerged {len(json_files)} file(s) into {output_path.name}")
    print(f"Total unique words: {len(merged)}")

    for json_file in json_files:
        try:
            json_file.unlink()
            print(f"Removed {json_file.name}")
        except OSError as e:
            print(f"Could not remove {json_file.name}: {e}")


if __name__ == "__main__":
    main()
