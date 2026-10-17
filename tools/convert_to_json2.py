#!/usr/bin/env python3
import sys
import mmap
import re
import json
from multiprocessing import Pool, cpu_count
import os


def parse_chunk(chunk_data):
    """Parse a chunk of HTML text and extract dictionary entries."""
    entries = {}

    entry_pattern = re.compile(r"<idx:entry[^>]*>(.*?)</idx:entry>", re.DOTALL | re.IGNORECASE)

    word_pattern = re.compile(r'<idx:orth\s+value="([^"]*)"', re.IGNORECASE)

    bold_pattern = re.compile(r"<b>(.*?)</b>", re.DOTALL)

    for entry_match in entry_pattern.finditer(chunk_data):
        entry_content = entry_match.group(1)

        # Get word from idx:orth value first, fallback to <b> tag
        word_match = word_pattern.search(entry_content)
        if word_match:
            word = word_match.group(1).strip()
        else:
            bold_match = bold_pattern.search(entry_content)
            if bold_match:
                word = re.sub(r"<[^>]+>", "", bold_match.group(1)).strip()
            else:
                continue

        if not word:
            continue

        # Extract definition
        definition = entry_content
        definition = re.sub(r"<idx:orth.*?</idx:orth>", "", definition, flags=re.DOTALL | re.IGNORECASE)
        definition = re.sub(r"<idx:infl.*?</idx:infl>", "", definition, flags=re.DOTALL | re.IGNORECASE)
        definition = re.sub(r"<b>.*?</b>", "", definition, flags=re.DOTALL)
        definition = re.sub(r"<[^>]+>", " ", definition)
        definition = re.sub(r"\s+", " ", definition).strip()

        if word and definition:
            entries[word] = definition

    return entries


def read_file_chunks(filepath, num_chunks=None):
    """Read file using mmap and split into chunks at safe boundaries."""
    if num_chunks is None:
        num_chunks = cpu_count()

    with open(filepath, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        if size == 0:
            return []

        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            chunk_size = size // num_chunks
            chunks = []
            start = 0

            for i in range(num_chunks):
                if i == num_chunks - 1:
                    end = size
                else:
                    target = start + chunk_size
                    pos = mm.find(b"<idx:entry", target)
                    end = pos if pos != -1 else size

                if start >= size:
                    break

                chunk_bytes = mm[start:end]
                chunks.append(chunk_bytes.decode("utf-8", errors="replace"))
                start = end

                if end >= size:
                    break

            return chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input.html> [output.json]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(input_file)[0] + ".json"

    print(f"Reading {input_file}...", file=sys.stderr)
    chunks = read_file_chunks(input_file)
    print(f"Split into {len(chunks)} chunks. Parsing in parallel...", file=sys.stderr)

    with Pool(processes=min(len(chunks), cpu_count())) as pool:
        results = pool.map(parse_chunk, chunks)

    # Merge dicts (later chunks override earlier on duplicates)
    entries = {}
    for chunk_result in results:
        entries.update(chunk_result)

    print(f"Extracted {len(entries)} entries. Writing to {output_file}...", file=sys.stderr)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
