import pandas as pd, glob

for f in sorted(glob.glob("*.pkl")):
    df = pd.read_pickle(f)
    print(f"\n=== {f} ===")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head(10).to_string())