import pandas as pd
import json
import glob
from pathlib import Path
from collections import OrderedDict

# ---- Config ----
LEVELS = [
    ("lab1.pkl", "level1_region"),
    ("lab2.pkl", "level2_country"),
    ("lab3.pkl", "level3_practice"),
]
OUT_JSON = "labels_merged.json"
OUT_TXT_DIR = "labels_by_level"  # one .txt per level, grouped by category
KEEP_STRIPPED = False  # set True to also include lab*s.pkl variants


def load_col(path, name):
    s = pd.read_pickle(path).iloc[:, 0]  # take the single column
    return s.rename(name)


def main():
    frames = []
    for fname, colname in LEVELS:
        path = Path(fname)
        if not path.exists():
            print(f"⚠ missing {fname}, skipping")
            continue
        frames.append(load_col(path, colname))

    # Row-aligned join (NOT concat) — same index from read_pickle
    df = pd.concat(frames, axis=1)
    print(f"Joined shape: {df.shape}")

    # Drop empty / null, strip whitespace
    df = df.apply(lambda c: c.astype(str).str.strip())
    df = df.replace({"": None, "nan": None, "None": None}).dropna()

    # Deduplicate on full combination
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Deduped: {before} → {len(df)} unique combinations")

    # ---- JSON: no "0" key, one record per unique combo ----
    records = json.loads(df.to_json(orient="records", force_ascii=False))
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✓ Wrote {len(records)} records to {OUT_JSON}")

    # ---- Text files: one per level, grouped by category ----
    outdir = Path(OUT_TXT_DIR)
    outdir.mkdir(exist_ok=True)

    for colname in df.columns:
        # Unique values for this level, sorted
        vals = sorted(df[colname].unique())

        # Plain flat file
        flat = outdir / f"{colname}.txt"
        flat.write_text("\n".join(vals) + "\n", encoding="utf-8")

        # Grouped file: level1 -> level2 -> level3 (only meaningful at deeper levels)
        # For level3, group by (level1, level2)
        if colname != df.columns[0]:
            grouped = OrderedDict()
            keys = list(df.columns[: df.columns.get_loc(colname)])
            for k, sub in df.groupby(keys, sort=True):
                if not isinstance(k, tuple):
                    k = (k,)
                grouped[" / ".join(k)] = sorted(sub[colname].unique())

            grp_file = outdir / f"{colname}_grouped.txt"
            with grp_file.open("w", encoding="utf-8") as f:
                for parent, children in grouped.items():
                    f.write(f"# {parent}\n")
                    for c in children:
                        f.write(f"  {c}\n")
                    f.write("\n")
            print(f"✓ {grp_file} ({len(grouped)} groups)")

        print(f"✓ {flat} ({len(vals)} unique)")


if __name__ == "__main__":
    main()
