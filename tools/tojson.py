import sys
import json
from pathlib import Path
from collections import defaultdict

input_path = Path(sys.argv[1])
output_path = input_path.with_suffix('.json')

# frequency -> list of words
freq_to_words = defaultdict(list)

with input_path.open(encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line.strip():
            continue
        # split on tab (or whitespace fallback)
        parts = line.split('\t')
        if len(parts) != 2:
            parts = line.split()
        word, freq = parts[0], int(parts[1])
        freq_to_words[freq].append(word)

# Sort frequencies descending, keep words in original order
result = {
    str(freq): freq_to_words[freq]
    for freq in sorted(freq_to_words.keys(), reverse=True)
}

with output_path.open('w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2,sort_keys=True)

print(f"Written: {output_path}")
