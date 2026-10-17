import json
import sys

# Get the input file path from command line argument
input_file = sys.argv[1]

# Read the JSON file
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Separate valid and failed records
valid_records = {}
failed_records = {}

for key, value in data.items():
    if key == value:
        # Key matches value, move to failed
        failed_records[key] = value
    else:
        # Key doesn't match value, keep in original
        valid_records[key] = value

# Write valid records back to the original file
with open(input_file, 'w', encoding='utf-8') as f:
    json.dump(valid_records, f, ensure_ascii=False, indent=2)

# Write failed records to failed.json
failed_file = input_file.replace('.json', '_failed.json')
with open(failed_file, 'w', encoding='utf-8') as f:
    json.dump(failed_records, f, ensure_ascii=False, indent=2)

print(f"Valid records: {len(valid_records)}")
print(f"Failed records: {len(failed_records)}")
print(f"Updated {input_file}")
print(f"Failed records saved to {failed_file}")
