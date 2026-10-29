import json
import os
import re
import subprocess

os.chdir("/opt/data/omakase-guide")

fish = json.load(open("fish.json"))
desc = json.load(open("descriptions.json"))
jr = json.load(open("journal.json"))

names = [x["j"] for x in fish]
print("fish:", len(fish), "| unique:", len(set(names)))

dupes = [n for n in set(names) if names.count(n) > 1]
print("duplicate fish names:", dupes)

missing_desc = [n for n in names if not desc.get(n)]
print("fish without description:", missing_desc)

jour = [e for e in jr if e.get("photo")]
bad_path = [e for e in jour if not os.path.exists(e["photo"])]
print("journal rows pointing at missing files:", [(e["kanji"], e["photo"]) for e in bad_path])

orphan_journal = [e["kanji"] for e in jr if e["kanji"] not in names]
print("journal kanji not in fish.json:", orphan_journal)

have = {e["kanji"] for e in jour}
print("no photo yet:", len([n for n in names if n not in have]))

used = {os.path.basename(e["photo"]) for e in jour}
allimg = {f for f in os.listdir("images/dish") if f.lower().endswith((".jpg", ".jpeg", ".png"))}
print("unused image files:", sorted(allimg - used))

# index.html freshness
subprocess.run(["/opt/data/trading-venv/bin/python3", "build_zen.py"], check=True)
print("git status:", subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip() or "(clean)")
sha = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True).stdout.strip()
print("HEAD:", sha)
