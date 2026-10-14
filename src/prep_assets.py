"""Подготовка ассетов товара из студийных фото (детерминированно, повторяемо).

Вход: google_drive/_MG_*.JPG (оригиналы пользователя, не изменяются).
Выход: assets/product/*.png|jpg — вырезки и крупные планы для слайдов.
"""
from __future__ import annotations

import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

G = "/home/user/graphic/google_drive/"
A = "/home/user/graphic/assets/product/"


def cutout(src: str, out: str, lum_min: float = 150, sat_max: float = 26,
           erode: int = 2, feather: float = 1.6, max_dim: int = 3000) -> Image.Image:
    """Светло-серый студийный фон -> прозрачность (фон, связанный с рамкой)."""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if max(im.size) > max_dim:
        k = max_dim / max(im.size)
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    lum, sat = a.mean(axis=2), a.max(axis=2) - a.min(axis=2)
    bg_like = (lum > lum_min) & (sat < sat_max)

    m = Image.fromarray(np.where(bg_like, 255, 0).astype(np.uint8), "L").copy()
    for corner in ((0, 0), (m.width - 1, 0), (0, m.height - 1), (m.width - 1, m.height - 1)):
        if m.getpixel(corner) == 255:
            ImageDraw.floodfill(m, corner, 128, thresh=0)
    bg_conn = np.asarray(m) == 128
    alpha = np.where(bg_conn, 0, 255).astype(np.uint8)

    am = Image.fromarray(alpha, "L")
    if erode:
        am = am.filter(ImageFilter.MinFilter(erode * 2 + 1))
    if feather:
        am = am.filter(ImageFilter.GaussianBlur(feather))

    img = im.convert("RGBA")
    img.putalpha(am)
    bbox = am.point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    img.save(out)
    print(f"  {os.path.basename(out)}: {img.size}")
    return img


def disc_geometry(jpg: str, max_dim: int = 1600):
    """Центр и радиус жёлтого диска на фото (по цвету рабочей стороны)."""
    im = ImageOps.exif_transpose(Image.open(jpg)).convert("RGB")
    k = max_dim / max(im.size)
    small = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    a = np.asarray(small).astype(np.int16)
    mask = ((a[..., 0] - a[..., 2]) > 28) & (a[..., 0] > 110)
    ys, xs = np.nonzero(mask)
    return im, (xs.mean() / k, ys.mean() / k, math.sqrt(mask.sum() / math.pi) / k, k)


def main() -> None:
    os.makedirs(A, exist_ok=True)
    print("вырезки товара:")
    cutout(G + "_MG_0459.JPG", A + "disc_front.png", lum_min=150, sat_max=30)
    cutout(G + "_MG_0457 (1).JPG", A + "disc_pair.png", lum_min=150, sat_max=30)
    cutout(G + "_MG_0452.JPG", A + "box_closed.png", lum_min=140, sat_max=24)
    cutout(G + "_MG_0465 (1).JPG", A + "box_open.png", lum_min=140, sat_max=24)

    print("крупные планы реального товара:")
    im, (cx, cy, R, k) = disc_geometry(G + "_MG_0459.JPG")
    # окно макро подбираем автоматически: кромка кадра не должна попадать на отверстие/фон
    best = None
    for scale in (0.34, 0.30, 0.26, 0.22):
        for ang_deg in (150, 165, 175, 185, 200, 215, 240, 270):
            ang = math.radians(ang_deg)
            S = int(scale * 2 * R)
            mx = cx + 0.76 * R * math.cos(ang)
            my = cy + 0.76 * R * math.sin(ang)
            box = (int(mx - S / 2), int(my - S / 2), int(mx + S / 2), int(my + S / 2))
            if box[0] < 0 or box[1] < 0 or box[2] > im.width or box[3] > im.height:
                continue
            c = np.asarray(im.crop(box)).astype(np.int16)
            lum = c.mean(axis=2)
            band = 0.07
            b = int(S * band)
            edges = np.concatenate([lum[:b].ravel(), lum[-b:].ravel(),
                                    lum[:, :b].ravel(), lum[:, -b:].ravel()])
            hole_like = (edges > 168).mean()                 # край отверстия/фон
            sat = ((c[..., 0] - c[..., 2]) > 28).mean()      # доля рабочей стороны
            score = sat - hole_like * 6
            if best is None or score > best[0]:
                best = (score, box, hole_like, sat, S)
    score, box, hole_like, sat, S = best
    print(f"  окно макро: {S}px, край-артефакты {hole_like*100:.2f}%, рабочая сторона {sat*100:.1f}%")
    crop = im.crop(box)
    crop = ImageEnhance.Sharpness(ImageEnhance.Contrast(crop).enhance(1.12)).enhance(1.3)
    crop.save(A + "macro_surface.jpg", quality=96)
    print(f"  macro_surface.jpg: {crop.size}")

    pair = ImageOps.exif_transpose(Image.open(G + "_MG_0457 (1).JPG")).convert("RGB")
    back = pair.crop((1500, 1600, 2950, 2500))
    ImageEnhance.Contrast(back).enhance(1.1).save(A + "macro_back.jpg", quality=95)
    print(f"  macro_back.jpg: {back.size}")
    holes = pair.crop((3350, 1400, 4350, 2200))
    holes.save(A + "holes_closeup.jpg", quality=95)
    print(f"  holes_closeup.jpg: {holes.size}")


if __name__ == "__main__":
    main()
