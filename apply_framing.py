#!/usr/bin/env python3
"""Apply consistent framing + exposure to the live dish photos.

Framing: crop a 3:4 window around the sushi so every piece occupies the same
share of the frame (SUBJECT_H). Boxes come from in-focus detection where it was
verified good, plus hand-checked overrides for the ones detection missed.

Exposure: after cropping, match the subject region's median Lab L / a / b to the
set median, so the food reads equally bright across cards.
"""
import json, os, shutil
import numpy as np
from PIL import Image
import normalize_photos as N

DISH = "/opt/data/omakase-guide/images/dish"
BACKUP = "/opt/data/omakase-backups/dish_orig/pre_norm"
SUBJECT_H = 0.55          # subject height as a share of the crop height
OUT_W, OUT_H = 960, 1280

# boxes the automatic detector got wrong — read off the photos by eye
OVERRIDE = {
    "akagai.jpg":    (0.25, 0.53, 0.88, 0.80),
    "aoriika.jpg":   (0.24, 0.375, 0.74, 0.735),
    "hirame.jpg":    (0.227, 0.548, 0.838, 0.803),
    "hokkigai.jpg":  (0.215, 0.535, 0.773, 0.802),
    "iwashi.jpg":    (0.255, 0.30, 0.64, 0.605),
    "kamasu.jpg":    (0.225, 0.355, 0.84, 0.605),
    "kinmedai.jpg":  (0.19, 0.495, 0.68, 0.815),
    "madai.jpg":     (0.265, 0.485, 0.61, 0.675),
    "shiraebi.jpg":  (0.33, 0.30, 0.72, 0.49),
    "sumiika.jpg":   (0.25, 0.42, 0.74, 0.73),
    "tokishirazu.jpg": (0.20, 0.41, 0.92, 0.75),
    "zuke.jpg":      (0.30, 0.42, 0.67, 0.66),
}


def box_for(f, path):
    if f in OVERRIDE:
        x0, y0, x1, y1 = OVERRIDE[f]
        return dict(x0=x0, x1=x1, y0=y0, y1=y1)
    b = N.subject_box(path)
    if not b:
        return dict(x0=0.15, x1=0.85, y0=0.25, y1=0.75)
    return b


def crop_around(im, b):
    W, H = im.size
    bh = (b["y1"] - b["y0"]) * H
    bw = (b["x1"] - b["x0"]) * W
    # window sized so the subject fills SUBJECT_H of the height (or width)
    ch = max(bh / SUBJECT_H, bw / (SUBJECT_H * 0.75), 1.0)
    ch = min(ch, H, W / 0.75)
    cw = ch * 0.75
    cx = (b["x0"] + b["x1"]) / 2 * W
    cy = (b["y0"] + b["y1"]) / 2 * H
    x0 = cx - cw / 2
    y0 = cy - ch / 2
    x0 = min(max(x0, 0), W - cw)
    y0 = min(max(y0, 0), H - ch)
    return im.crop((int(round(x0)), int(round(y0)),
                    int(round(x0 + cw)), int(round(y0 + ch)))).resize((OUT_W, OUT_H), Image.LANCZOS)


def main():
    jr = json.load(open("/opt/data/omakase-guide/journal.json"))
    live = sorted({os.path.basename(e["photo"]) for e in jr if e.get("photo")})
    os.makedirs(BACKUP, exist_ok=True)
    tmp = "/opt/data/omakase-backups/dish_work"
    os.makedirs(tmp, exist_ok=True)

    # 1) crop
    print(f"{'file':22s} {'box source':10s} subject share")
    for f in live:
        p = os.path.join(DISH, f)
        im = Image.open(p).convert("RGB")
        b = box_for(f, p)
        out = crop_around(im, b)
        out.save(os.path.join(tmp, f), quality=95)
        print(f"{f:22s} {'manual' if f in OVERRIDE else 'auto':10s} h={(b['y1']-b['y0']):.2f}")

    # 2) exposure target from the cropped subject region (centre is the subject now)
    st = {f: N._centre_stats(os.path.join(tmp, f)) for f in live}
    tgt = {k: float(np.median([v[k] for v in st.values()])) for k in ("L", "a", "b")}
    print(f"\ntarget L={tgt['L']:.1f} a={tgt['a']:.1f} b={tgt['b']:.1f}")
    print("before:", {f[:-4]: round(st[f]['L'], 1) for f in live})

    for f in live:
        shutil.copy(os.path.join(DISH, f), os.path.join(BACKUP, f))
        norm = N.normalise_image(os.path.join(tmp, f), tgt)
        norm.save(os.path.join(DISH, f), quality=93)
    after = {f: N._centre_stats(os.path.join(DISH, f)) for f in live}
    print("after :", {f[:-4]: round(after[f]['L'], 1) for f in live})
    ls = sorted(after[f]["L"] for f in live)
    print(f"\nafter L spread: min {ls[0]:.1f} median {ls[len(ls)//2]:.1f} max {ls[-1]:.1f}")


if __name__ == "__main__":
    main()
