from PIL import Image, ImageDraw, ImageFont

Fz = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
fnt = ImageFont.truetype(Fz, 22)
items = [
    ("kanpyo.jpg", "乾瓢巻（新條目）"),
    ("tamago.jpg", "玉子（玉子焼）"),
    ("akauni.jpg", "赤雲丹（赤海膽）"),
    ("ankimo.jpg", "鮟肝（あん肝）"),
    ("zuwai.jpg", "ズワイガニ（松葉蟹）"),
]
tw, th, cap = 340, 453, 36
sh = Image.new("RGB", (len(items) * tw, th + cap + 50), "white")
dr = ImageDraw.Draw(sh)
dr.rectangle([0, 0, len(items) * tw, 44], fill="#f3ecdd")
dr.text((12, 8), "本輪入站 5 張", fill="#2a241c", font=ImageFont.truetype(Fz, 26))
for i, (f, l) in enumerate(items):
    im = Image.open("images/dish/" + f).convert("RGB").resize((tw, th))
    sh.paste(im, (i * tw, 50))
    dr.text((i * tw + 6, th + 56), l, fill="#a00", font=fnt)
sh.save("/opt/data/cache/scratch/batch2_used.jpg", quality=90)
print("ok", sh.size)
