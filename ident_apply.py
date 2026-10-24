import json, os, shutil
BASE="/opt/data/omakase-guide"; D="/opt/data/cache/images"
res=json.load(open(f"{BASE}/ident_results.json",encoding="utf-8"))
entries=json.load(open(f"{BASE}/entries.json",encoding="utf-8"))
journal=json.load(open(f"{BASE}/journal.json",encoding="utf-8"))
have={e["kanji"] for e in journal}

# group by identified fish
best={}
other=[]; low=[]
for f,o in res.items():
    if o.get("not_fish"): 
        other.append((f,o.get("jp","?"),o.get("confidence",0))); continue
    jp=(o.get("jp") or "").strip()
    if not jp or jp=="OTHER":
        other.append((f,jp or "?",o.get("confidence",0))); continue
    if jp not in entries:
        other.append((f,jp,o.get("confidence",0))); continue
    c=o.get("confidence",0)
    if c < 60:
        low.append((f,jp,c)); continue
    if jp not in best or c>best[jp][1]:
        best[jp]=(f,c,o)

written=[]
for jp,(f,c,o) in best.items():
    rom=entries[jp]["r"]
    dst=f"images/dish/{rom}.jpg"
    shutil.copy(f"{D}/{f}", f"{BASE}/{dst}")
    if jp not in have:
        journal.append({"date":"","venue":"","kanji":jp,"photo":dst})
        have.add(jp)
    else:
        for e in journal:
            if e["kanji"]==jp: e["photo"]=dst
    written.append((jp,f,c))

json.dump(journal, open(f"{BASE}/journal.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("assigned fishes:",len(written))
print("journal total:",len(journal))
print("\nLOW CONFIDENCE (<65):",len(low))
for f,j,c in low[:40]: print(f"  {f} -> {j} ({c})")
print("\nOTHER / NOT FISH:",len(other))
for f,j,c in other[:40]: print(f"  {f} -> {j} ({c})")
