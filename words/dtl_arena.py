#!/usr/bin/env python3
"""Detect Persian dictionary entries whose English value is transliteration.

Expected input format:
    {"علی": "Ali", "خانه": "house"}

With --move, detected entries are removed from the source output and written
as a second JSON object. The input file itself is never overwritten unless
--in-place is supplied.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    # Run from the installed package/project root.
    from p2f import dictionary as p2f_dictionary
    from p2f import p2f_word
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Could not import p2f. Install the package or run this script from "
        "the project root."
    ) from exc


# Arabic/Persian presentation differences should not prevent a match.
_TRANSLIT_RE = re.compile(r"[^a-z0-9]+", re.IGNORECASE)


def canonical(value: str) -> str:
    """Return a comparison form for transliterations."""
    value = value.casefold().replace("ي", "ی").replace("ك", "ک")
    return _TRANSLIT_RE.sub("", value)


def candidate_transliterations(
    persian: str, *, max_word_size: int = 15, cutoff: int = 50
) -> set[str]:
    """Get all likely Finglish spellings for a Persian key."""
    candidates = {
        canonical(candidate)
        for candidate, _score in p2f_word(
            persian, max_word_size=max_word_size, cutoff=cutoff
        )
        if candidate
    }

    # p2f-dict.txt stores multiple spellings on one line, for example
    # ``عاشق ashegh asheq``. p2f_word intentionally returns that whole value
    # as one dictionary result, so add each spelling separately here.
    for spelling in str(p2f_dictionary.get(persian, "")).split():
        candidates.add(canonical(spelling))
    return candidates


def is_transliteration(
    persian: str,
    english_value: Any,
    *,
    max_word_size: int = 15,
    cutoff: int = 50,
) -> bool:
    """Return True when a value exactly matches a p2f transliteration.

    A list value is considered transliterated if at least one string in it is
    a transliteration. Non-string values are ignored.
    """
    if isinstance(english_value, str):
        values = [english_value]
    elif isinstance(english_value, list):
        values = [item for item in english_value if isinstance(item, str)]
    else:
        return False

    candidates = candidate_transliterations(
        persian, max_word_size=max_word_size, cutoff=cutoff
    )
    return any(canonical(value) in candidates for value in values)


def detect(
    data: dict[str, Any], *, max_word_size: int = 15, cutoff: int = 50
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split an object mapping into (normal_entries, transliterated_entries)."""
    normal: dict[str, Any] = {}
    transliterated: dict[str, Any] = {}

    for persian, value in data.items():
        if not isinstance(persian, str):
            normal[persian] = value
        elif is_transliteration(
            persian, value, max_word_size=max_word_size, cutoff=cutoff
        ):
            transliterated[persian] = value
        else:
            normal[persian] = value

    return normal, transliterated


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect Finglish/transliterated values in a Persian-English JSON object."
    )
    parser.add_argument("input", type=Path, help="Input JSON object")
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Output JSON for the non-transliterated dictionary (default: stdout)",
    )
    parser.add_argument(
        "-m", "--move", action="store_true",
        help="Write detected entries to a separate JSON file and remove them from the output",
    )
    parser.add_argument(
        "--moved-output", type=Path,
        help="Path for moved entries (default: <input>.transliterated.json)",
    )
    parser.add_argument(
        "--in-place", action="store_true",
        help="With --move, replace the input file with the filtered dictionary",
    )
    parser.add_argument("--max-word-size", type=int, default=15)
    parser.add_argument(
        "--cutoff", type=int, default=50,
        help="Number of p2f alternatives checked per Persian key (default: 50)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.in_place and not args.move:
        raise SystemExit("--in-place requires --move")

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("input JSON must be an object mapping Persian words to values")

    normal, moved = detect(
        data, max_word_size=args.max_word_size, cutoff=args.cutoff
    )

    if args.move:
        moved_path = args.moved_output or args.input.with_name(
            args.input.stem + ".transliterated.json"
        )
        write_json(moved_path, moved)
        output_data = normal
        if args.in_place:
            output_path = args.input
        elif args.output:
            output_path = args.output
        else:
            output_path = args.input.with_name(args.input.stem + ".filtered.json")
        write_json(output_path, output_data)
        print(f"Detected and moved {len(moved)} entries to {moved_path}", file=sys.stderr)
        print(f"Wrote {len(normal)} remaining entries to {output_path}", file=sys.stderr)
    elif args.output:
        # Without --move, write a report containing both groups.
        write_json(args.output, {"transliterated": moved, "other": normal})
        print(f"Detected {len(moved)} transliterated entries", file=sys.stderr)
    else:
        json.dump(
            {"transliterated": moved, "other": normal},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
