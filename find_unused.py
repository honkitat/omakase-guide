import hashlib
import json
import os

os.chdir("/opt/data/omakase-guide")
STORE = "/opt/data/omakase-backups/photos_all"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


jr = json.load(open("journal.json"))
used_files = [e["photo"] for e in jr if e.get("photo")]
used = {}
for p in used_files:
    used[md5(p)] = os.path.basename(p)

store = {}
for f in sorted(os.listdir(STORE)):
    if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        continue
    p = os.path.join(STORE, f)
    store.setdefault(md5(p), []).append(f)

unused = {k: v for k, v in store.items() if k not in used}
print("used images:", len(used), "| store unique:", len(store), "| store files:", sum(len(v) for v in store.values()))
print("unused unique:", len(unused))

cache = "/opt/data/cache/images"
cache_hit = 0
rows = []
for h, names in unused.items():
    live = None
    for f in os.listdir(cache):
        cp = os.path.join(cache, f)
        if os.path.isfile(cp) and md5(cp) == h:
            live = cp
            cache_hit += 1
            break
    rows.append({"md5": h, "store": names[0], "path": live or os.path.join(STORE, names[0])})

print("resolvable in live cache:", cache_hit, "/", len(unused))
json.dump(rows, open("/opt/data/cache/scratch/unused_photos.json", "w"), ensure_ascii=False, indent=1)
for i, r in enumerate(rows[:80], 1):
    print(i, os.path.basename(r["path"]))
