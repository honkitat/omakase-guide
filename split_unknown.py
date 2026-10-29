import json
import os

rows = json.load(open("/opt/data/cache/scratch/unused_photos.json"))
ids = json.load(open("/opt/data/omakase-guide/photo_ids.json"))
known = set(ids.keys())

unknown = []
labelled = []
for r in rows:
    fn = os.path.basename(r["path"])
    if fn in known:
        labelled.append((fn, ids[fn].get("jjh")))
    else:
        unknown.append(r)

print("unused total:", len(rows))
print("already labelled (jjh 已講過):", len(labelled))
print("never seen:", len(unknown))
json.dump(unknown, open("/opt/data/cache/scratch/unknown_photos.json", "w"), ensure_ascii=False, indent=1)

# which fish still have no photo
fish = json.load(open("/opt/data/omakase-guide/fish.json"))
jr = json.load(open("/opt/data/omakase-guide/journal.json"))
have = {e["kanji"] for e in jr if e.get("photo")}
empty = [x["j"] for x in fish if x["j"] not in have]
print("empty slots:", len(empty))
print(" | ".join(empty))
