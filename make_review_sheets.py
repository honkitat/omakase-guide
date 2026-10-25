#!/usr/bin/env python3
"""Build per-dish candidate review sheets from jjh's original photo dump.

One PNG per dish group: every photo the identification pass tagged with that
label, numbered left-to-right / top-to-bottom, with the currently-used one
framed in green and marked 現用. jjh replies with a number.
"""
import json, hashlib, os, collections
from PIL import Image, ImageDraw, ImageFont

SRC = "/opt/data/cache/images"
DISH = "/opt/data/omakase-guide/images/dish"
OUT = "/opt/data/cache/scratch/review"
os.makedirs(OUT, exist_ok=True)

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FJ = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def font(sz, jp=False):
    try:
        return ImageFont.truetype(FJ if jp else F, sz)
    except Exception:
        return ImageFont.load_default()


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


used = {}
_jr = json.load(open("/opt/data/omakase-guide/journal.json"))
_refd = {os.path.basename(e["photo"]) for e in _jr if e.get("photo")}
for f in os.listdir(DISH):
    if f.lower().endswith((".jpg", ".jpeg", ".png")) and f in _refd:
        used[md5(os.path.join(DISH, f))] = f

ident = json.load(open("/opt/data/omakase-guide/ident_results.json"))
groups = collections.defaultdict(list)
for fn, v in ident.items():
    p = os.path.join(SRC, fn)
    if v.get("not_fish") or not os.path.exists(p):
        continue
    groups[v.get("jp", "?")].append((fn, used.get(md5(p), ""), v.get("confidence", 0)))

# only groups that actually offer a choice
groups = {k: v for k, v in groups.items() if len(v) >= 2}
order = sorted(groups, key=lambda k: -len(groups[k]))


def build(label, rows):
    cols = 4 if len(rows) > 6 else len(rows)
    tw, th, cap, hd = 300, 400, 34, 74
    nr = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, hd + nr * (th + cap)), "white")
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([0, 0, cols * tw, hd - 8], fill="#f3ecdd")
    dr.text((12, 10), f"{label}", fill="#2a241c", font=font(38, True))
    dw = dr.textlength(label, font=font(38, True))
    dr.text((16 + dw, 18), f"{len(rows)} 張候選 · 回覆號碼 · 綠框=現用",
            fill="#8a6f3f", font=font(22, True))
    for i, (fn, u, conf) in enumerate(rows):
        im = Image.open(os.path.join(SRC, fn)).convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, hd + (i // cols) * (th + cap)
        sheet.paste(im, (x, y))
        box = [x + 2, y + 2, x + tw - 3, y + th - 3]
        if u:
            dr.rectangle(box, outline="#1a7f37", width=7)
            dr.rectangle([x + 2, y + 2, x + 96, y + 34], fill="#1a7f37")
            dr.text((x + 10, y + 6), "現用", fill="white", font=font(22, True))
        else:
            dr.rectangle(box, outline="#bbbbbb", width=2)
        dr.text((x + 8, y + th + 4), f"{i+1}", fill="#a00", font=font(22))
        tag = f"  {u}" if u else ""
        dr.text((x + 36, y + th + 8), f"{fn[4:12]}{tag}", fill="#333", font=font(14))
    p = os.path.join(OUT, f"{len(order)-order.index(label):02d}_{label}.png")
    sheet.save(p, quality=90)
    return p, len(rows)


manifest = []
for label in order:
    rows = sorted(groups[label], key=lambda r: (r[1] == "", -r[2]))
    p, n = build(label, rows)
    manifest.append({"label": label, "n": n, "path": p,
                     "used": [r[1] for r in rows if r[1]],
                     "cands": [r[0] for r in rows]})
    print(f"{os.path.basename(p):28s} {n} 張   used={[r[1] for r in rows if r[1]]}")

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print(f"\n{len(manifest)} groups -> {OUT}")
