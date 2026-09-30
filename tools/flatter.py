import json
import re

INPUT_JSON = "lab.json"
OUTPUT_TXT = "values.txt"


def main():
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Collect values from each record. Handles:
    #   - dicts like {"0": "value"}
    #   - dicts with multiple keys (all values taken)
    #   - plain strings/numbers
    values = []
    for record in data:
        if isinstance(record, dict):
            # Sort keys so "0", "1", "2" come out in order
            for key in sorted(record.keys(), key=lambda k: (len(str(k)), str(k))):
                val = record[key]
                if val is None:
                    continue
                values.append(str(val))
        elif record is not None:
            values.append(str(record))

    # Optional: strip whitespace, drop empties, dedupe (order preserved)
    seen = set()
    cleaned = []
    for v in values:
        v = v.strip()
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        cleaned.append(v)

    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write("\n".join(cleaned))
        if cleaned:
            f.write("\n")

    print(f"✓ Wrote {len(cleaned)} unique values to {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
