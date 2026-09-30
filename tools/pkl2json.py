import pandas as pd
import pickle
import json
import glob
from pathlib import Path

def load_pkl_file(filepath):
    """Load a pickle file and return the DataFrame."""
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        if not isinstance(data, pd.DataFrame):
            print(f"Warning: {filepath} does not contain a DataFrame (got {type(data)}). Skipping.")
            return None

        print(f"Loaded {filepath}: {len(data)} rows, {len(data.columns)} columns")
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def main():
    pkl_files = sorted(glob.glob("*.pkl"))

    if not pkl_files:
        print("No .pkl files found in current directory.")
        return

    print(f"Found {len(pkl_files)} pickle file(s):\n")
    for f in pkl_files:
        print(f"  - {f}")
    print()

    outdir = Path("json_out")
    outdir.mkdir(exist_ok=True)

    for filepath in pkl_files:
        df = load_pkl_file(filepath)
        if df is None:
            continue

        # Drop duplicates for this file only
        before = len(df)
        df = df.drop_duplicates()
        print(f"  deduped: {before} → {len(df)}")

        # Take the single column (assumes column '0' exists; falls back to first col)
        col = df["0"] if "0" in df.columns else df.iloc[:, 0]

        # Extract values: strip whitespace, drop nulls/empties, dedupe, sort
        values = col.dropna().astype(str).str.strip()
        values = values[values != ""]
        values = sorted(set(values))

        # Write as a plain JSON array of strings (no "0" key)
        out_file = outdir / (Path(filepath).stem + ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(values, f, ensure_ascii=False, indent=2)

        print(f"✓ Wrote {len(values)} unique values to {out_file}\n")


if __name__ == "__main__":
    main()