from __future__ import annotations

import json
import sys


def main():

    input_file = sys.argv[1]
    output_file = input_file

    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = {item["source"]: item["translation"] for item in data["translations"]}

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print(f"Converted successfully: {output_file}")


if __name__ == "__main__":
    main()
