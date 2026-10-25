#!/usr/bin/env python3
"""Apply jjh's review pick: `python3 pick.py <label> <n>`

Copies the chosen original into images/dish/<current-file>.jpg, backing up the
previous one to images/dish/orig/, then rebuilds index.html.
"""
import json, os, shutil, subprocess, sys

BASE = "/opt/data/omakase-guide"
SRC = "/opt/data/cache/images"
man = json.load(open("/opt/data/cache/scratch/review/manifest.json"))
journal = json.load(open(f"{BASE}/journal.json"))

label, n = sys.argv[1], int(sys.argv[2])
grp = next(g for g in man if g["label"] == label)
pick = grp["cands"][n - 1]
target = grp["used"][0] if grp["used"] else None

if not target:
    print(f"NOTE: {label} has no photo in use yet — need a filename to create.")
    target = sys.argv[3] if len(sys.argv) > 3 else None
    if not target:
        sys.exit("pass a target filename, e.g. `pick.py {label} {n} shimaaji.jpg`")

dst = f"{BASE}/images/dish/{target}"
os.makedirs(f"{BASE}/images/dish/orig", exist_ok=True)
if os.path.exists(dst):
    shutil.copy(dst, f"{BASE}/images/dish/orig/{target.replace('.jpg','_old.jpg')}")
shutil.copy(f"{SRC}/{pick}", dst)
print(f"{label} #{n}: {pick} -> images/dish/{target}")

# make sure journal points at it
changed = False
for e in journal:
    if os.path.basename(e.get("photo", "")) == target:
        changed = False  # already referenced
        break
print(subprocess.run(["/opt/data/trading-venv/bin/python3", f"{BASE}/build_zen.py"],
                     capture_output=True, text=True).stdout.strip())
