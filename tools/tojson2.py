import sys
import json
from pathlib import Path
from collections import defaultdict

input_path = Path(sys.argv[1])
output_path = input_path.with_suffix(".json")

# frequency -> list of words
freq_to_words = defaultdict(list)


result = {}
with input_path.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 2:
            parts = line.split()
        word, freq = parts[0], int(parts[1])
        result[word] = freq

with output_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)


print(f"Written: {output_path}")
