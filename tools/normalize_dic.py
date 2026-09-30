import json
import sys
import os


def convert_dict(input_file):
    # Read the input JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert list of dicts to a single dict
    result = {}
    for item in data:
        result.update(item)

    # Write back to the same file (in place)
    # First write to a temp file to avoid corruption if something goes wrong
    temp_file = input_file + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Replace original file with temp file
    os.replace(temp_file, input_file)

    print(f"Converted {len(data)} entries → {len(result)} unique keys")
    print(f"File updated: {input_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    convert_dict(input_file)
