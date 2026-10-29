import json
import os

from PIL import Image, ImageDraw, ImageFont

Fz = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
rows = json.load(open("/opt/data/cache/scratch/unknown_photos.json"))
fnt = ImageFont.truetype(Fz, 20)
picks = [3, 7, 43, 45, 50]
proposal = {
    3: "→ 鯖（バッテラ押し寿司）",
    7: "→ 鯖（しめ鯖刺身）",
    43: "→ 甘鯛／カレイ／スズキ？",
    45: "→ 緣側（えんがわ）？",
    50: "→ カワハギ（已有相，重複）",
}
tw, th, cap = 330, 440, 60
sh = Image.new("RGB", (len(picks) * tw, th + cap + 50), "white")
dr = ImageDraw.Draw(sh)
dr.rectangle([0, 0, len(picks) * tw, 46], fill="#f3ecdd")
dr.text((14, 8), "可用嘅相（其餘 47 張唔係壽司）", fill="#2a241c", font=ImageFont.truetype(Fz, 26))
for i, n in enumerate(picks):
    r = rows[n - 1]
    im = Image.open(r["path"]).convert("RGB").resize((tw, th))
    sh.paste(im, (i * tw, 50))
    dr.text((i * tw + 8, th + 56), f"#{n}", fill="#a00", font=ImageFont.truetype(Fz, 26))
    dr.text((i * tw + 8, th + 84), proposal[n], fill="#333", font=fnt)
sh.save("/opt/data/cache/scratch/proposal_sheet.jpg", quality=90)
print("ok", sh.size)
