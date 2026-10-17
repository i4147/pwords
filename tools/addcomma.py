from __future__ import annotations


def convert_first_space_in_quotes(filename, start_line=160):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()

        for i in range(start_line - 1, len(lines)):
            line = lines[i]

            first_quote_pos = line.find('"')
            if first_quote_pos != -1:
                second_quote_pos = line.find('"', first_quote_pos + 1)
                if second_quote_pos != -1:
                    content_start = first_quote_pos + 1
                    content_end = second_quote_pos
                    content = line[content_start:content_end]

                    first_space_pos = content.find(" ")
                    if first_space_pos != -1:
                        new_content = content[:first_space_pos] + ", " + content[first_space_pos + 1 :]

                        line = line[:content_start] + new_content + line[content_end:]
                        lines[i] = line

        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(lines)

        print(f"Successfully processed file from line {start_line} to end")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]

    convert_first_space_in_quotes(filename, start_line=135)
