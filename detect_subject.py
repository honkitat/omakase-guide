#!/usr/bin/env python3
"""Subject (sushi) detection for card framing.

Spectral-residual saliency (Hou & Zhang 2007) — robust for a single salient
object on a textured plate/counter. Returns a bbox per image plus a normalised
crop window that centres the subject at a consistent scale.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

DISH = "/opt/data/omakase-guide/images/dish"
OUT = "/opt/data/omakase-guide/framing.json"
N = 160  # analysis resolution


def saliency(img):
    g = img.convert("L").resize((N, N), Image.LANCZOS)
    a = np.asarray(g).astype(np.float32) / 255.0
    # small blur to suppress pixel noise before FFT
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                   dtype=np.float32) / 255.0
    F = np.fft.fft2(a)
    amp = np.abs(F)
    phase = np.angle(F)
    logamp = np.log(amp + 1e-8)
    # 3x3 mean of log amplitude
    from numpy.lib.stride_tricks import sliding_window_view
    k = 3
    pad = np.pad(logamp, k // 2, mode="edge")
    win = sliding_window_view(pad, (k, k))
    avg = win.mean(axis=(-1, -2))
    resid = logamp - avg
    sal = np.abs(np.fft.ifft2(np.exp(resid + 1j * phase))) ** 2
    sal = sal - sal.min()
    sal = sal / (sal.max() + 1e-8)
    s8 = Image.fromarray((sal * 255).astype(np.uint8))
    sal = np.asarray(s8.filter(ImageFilter.GaussianBlur(6.0)), dtype=np.float32) / 255.0
    sal = (sal - sal.min()) / (sal.max() - sal.min() + 1e-8)
    return sal


def bbox(sal, q=90):
    thr = np.percentile(sal, q)
    m = sal >= thr
    # keep the largest connected component (4-neighbour BFS via scipy-free labelling)
    lab = np.zeros(m.shape, np.int32)
    cur = 0
    best = (0, None)
    ys, xs = np.nonzero(m)
    seen = np.zeros(m.shape, bool)
    from collections import deque
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        cur += 1
        dq = deque([(y0, x0)])
        seen[y0, x0] = True
        pts = []
        while dq:
            y, x = dq.popleft()
            pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    dq.append((ny, nx))
        if len(pts) > best[0]:
            best = (len(pts), pts)
    if not best[1] or best[0] < 60:
        return None
    p = np.array(best[1])
    y0, y1 = p[:, 0].min(), p[:, 0].max()
    x0, x1 = p[:, 1].min(), p[:, 1].max()
    # weighted centroid of saliency inside the blob
    sub = sal[y0:y1 + 1, x0:x1 + 1]
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    w = sub / (sub.sum() + 1e-8)
    return {
        "x0": round(x0 / N, 4), "x1": round((x1 + 1) / N, 4),
        "y0": round(y0 / N, 4), "y1": round((y1 + 1) / N, 4),
        "cx": round(float((xx * w).sum()) / N, 4),
        "cy": round(float((yy * w).sum()) / N, 4),
        "bw": round((x1 - x0 + 1) / N, 4), "bh": round((y1 - y0 + 1) / N, 4),
    }


def main():
    out, overlay = {}, {}
    files = [f for f in sorted(os.listdir(DISH)) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    for f in files:
        p = os.path.join(DISH, f)
        img = Image.open(p).convert("RGB")
        b = bbox(saliency(img))
        if b is None:
            print(f"{f:24s} FAIL")
            continue
        out[f] = b
        overlay[f] = (b, img)
        print(f"{f:24s} cx={b['cx']:.2f} cy={b['cy']:.2f} bw={b['bw']:.2f} bh={b['bh']:.2f}")
    json.dump(out, open(OUT, "w"), indent=1, sort_keys=True)

    # proof sheet with boxes drawn
    cols, tw, th = 5, 220, 293
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 16)), "white")
    dr = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        if f not in overlay:
            continue
        b, img = overlay[f]
        im = img.resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + 16)
        sheet.paste(im, (x, y))
        dr.rectangle([x + b["x0"] * tw, y + b["y0"] * th, x + b["x1"] * tw, y + b["y1"] * th],
                     outline="red", width=2)
        dr.ellipse([x + b["cx"] * tw - 3, y + b["cy"] * th - 3, x + b["cx"] * tw + 3, y + b["cy"] * th + 3],
                   fill="lime")
        dr.text((x + 4, y + th + 2), f"{i+1}. {f[:-4]}", fill="black")
    sheet.save("/opt/data/cache/scratch/frames/detect_proof.jpg", quality=85)
    print("\nproof -> /opt/data/cache/scratch/frames/detect_proof.jpg")


if __name__ == "__main__":
    main()
