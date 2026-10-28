from PIL import Image, ImageDraw, ImageFont

Fz = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
fnt = ImageFont.truetype(Fz, 24)
items = [
    ("/opt/data/omakase-backups/dish_orig/pre_norm/sanma.jpg", "1 現用 B  img_fc01a4c8"),
    ("/opt/data/omakase-backups/dish_orig/sanma_old.jpg", "2 舊 A  img_20a89a55"),
    ("/opt/data/cache/images/img_f2af6dd829de.jpg", "3 新 #4  img_f2af6dd8"),
    ("/opt/data/cache/images/img_c21ca242a6eb.jpg", "4 新 #8  img_c21ca242"),
]
tw, th, cap = 340, 453, 40
sh = Image.new("RGB", (4 * tw, th + cap + 50), "white")
dr = ImageDraw.Draw(sh)
dr.rectangle([0, 0, 4 * tw, 44], fill="#f3ecdd")
dr.text((12, 8), "秋刀魚 4 張候選", fill="#2a241c", font=ImageFont.truetype(Fz, 26))
for i, (p, l) in enumerate(items):
    im = Image.open(p).convert("RGB").resize((tw, th))
    sh.paste(im, (i * tw, 50))
    dr.text((i * tw + 8, th + 56), f"{i+1}. {l}", fill="#a00", font=fnt)
sh.save("/opt/data/cache/scratch/sanma_pick2.jpg", quality=90)
print("ok", sh.size)
