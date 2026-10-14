"""Сборка серии: PNG каждого слайда, общий ZIP, PDF-предпросмотр, контакт-лист."""
from __future__ import annotations

import os
import zipfile
from PIL import Image

import ds
from slides_v2 import s01, s02, s03, s04, s05, s06, s07

OUT = "/home/user/graphic/final_v02"
SLIDES = [
    ("S01", "Обложка", s01),
    ("S02", "Применение", s02),
    ("S03", "Зернистость P100", s03),
    ("S04", "8 отверстий", s04),
    ("S05", "Крупный план", s05),
    ("S06", "Размер и упаковка", s06),
    ("S07", "Финал серии", s07),
]
VERSION = "v02"
FILE_BASE = "OneLite_Gold_125mm_P100"


def main():
    os.makedirs(OUT, exist_ok=True)
    pngs = []
    for code, title, fn in SLIDES:
        img = fn().convert("RGB")
        assert img.size == (ds.W, ds.H), (code, img.size)
        path = f"{OUT}/{FILE_BASE}_{code}_{VERSION}.png"
        img.save(path, "PNG", optimize=True)
        pngs.append(path)
        print("ok", os.path.basename(path))

    # ZIP с отдельными слайдами
    zpath = f"{OUT}/{FILE_BASE}_S01-S07_{VERSION}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in pngs:
            z.write(p, os.path.basename(p))
    print("ok", os.path.basename(zpath))

    # PDF-предпросмотр
    ims = [Image.open(p).convert("RGB") for p in pngs]
    pdf = f"{OUT}/{FILE_BASE}_S01-S07_{VERSION}_preview.pdf"
    ims[0].save(pdf, save_all=True, append_images=ims[1:], resolution=150.0)
    print("ok", os.path.basename(pdf))

    # контакт-лист для проверки серии
    tw_, th_ = 420, 562
    sheet = Image.new("RGB", (tw_ * 4 + 50, th_ * 2 + 40), (24, 24, 24))
    for i, im in enumerate(ims):
        thumb = im.resize((tw_, th_), Image.LANCZOS)
        sheet.paste(thumb, (10 + (i % 4) * (tw_ + 10), 10 + (i // 4) * (th_ + 10)))
    sheet.save(f"{OUT}/_contact_sheet_{VERSION}.png")
    print("ok contact sheet")


if __name__ == "__main__":
    main()
