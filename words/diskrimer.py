nl = []
ha = []
with open("big.txt", encoding="utf-8") as f:
    for line in f:
        striped = line.strip()
        if not striped.endswith("ها"):
            nl.append(line)
        else:
            ha.append(line)

with open("big2.txt", "w", encoding="utf-8") as f:
    for k in nl:
        f.write(k)
with open("ha.txt", "w", encoding="utf-8") as f:
    for k in ha:
        f.write(k)
