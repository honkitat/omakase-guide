import json
import os

from PIL import Image, ImageDraw, ImageFont

Fz = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
rows = json.load(open("/opt/data/cache/scratch/unknown_photos.json"))
OUT = "/opt/data/cache/scratch"
PER = 12
COLS = 4
tw, th, cap = 330, 440, 34

for s in range(0, len(rows), PER):
    chunk = rows[s:s + PER]
    nrows = (len(chunk) + COLS - 1) // COLS
    img = Image.new("RGB", (COLS * tw, nrows * (th + cap) + 50), "white")
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, COLS * tw, 46], fill="#f3ecdd")
    dr.text((14, 8), f"未鑑定相 #{s+1}-{s+len(chunk)} / {len(rows)}", fill="#2a241c",
            font=ImageFont.truetype(Fz, 26))
    for i, r in enumerate(chunk):
        try:
            im = Image.open(r["path"]).convert("RGB")
        except Exception as e:
            print("skip", r["path"], e)
            continue
        im = im.resize((tw, th))
        x = (i % COLS) * tw
        y = 50 + (i // COLS) * (th + cap)
        img.paste(im, (x, y))
        dr.text((x + 8, y + th + 4), f"#{s+i+1}", fill="#a00", font=ImageFont.truetype(Fz, 28))
    p = f"{OUT}/unknown_{s//PER+1}.jpg"
    img.save(p, quality=88)
    print(p, img.size)
