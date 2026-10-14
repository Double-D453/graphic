"""Дополнительные UI-элементы для серии v02: стеклянные панели, строка характеристик,
верхняя строка с чипом линейки и логотипом бренда (приём взят из референсов пользователя).
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from ds import (GOLD, GRAY_D, LINE, M, W, WHITE, F, tw)

__all__ = ["glass_panel", "param_strip", "brand_bar", "chip"]


def glass_panel(img: Image.Image, box, radius: int = 30, blur: float = 24,
                tint=(255, 255, 255, 20), border=(255, 255, 255, 74),
                hi=(255, 255, 255, 40), width: int = 3):
    """Матовая «стеклянная» панель: размытие фона + полупрозрачный слой + рамка."""
    x0, y0, x1, y1 = [int(v) for v in box]
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)

    region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    blurred = img.copy()
    blurred.paste(region, (x0, y0))
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    base.paste(blurred, (0, 0), mask)
    img.alpha_composite(base)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=tuple(tint))
    img.alpha_composite(layer)

    hl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(hl)
    dh.rounded_rectangle([x0 + 12, y0 + 7, x1 - 12, y0 + 11], radius=5, fill=tuple(hi))
    hl.putalpha(Image.composite(hl.getchannel("A"), Image.new("L", img.size, 0), mask))
    img.alpha_composite(hl)

    ImageDraw.Draw(img).rounded_rectangle(box, radius=radius, outline=tuple(border),
                                          width=width)
    return img


def chip(d: ImageDraw.ImageDraw, xy, s: str, font, fg=(18, 22, 24),
         bg=(250, 250, 248), pad_x: int = 34, pad_y: int = 20, radius: int = 18):
    x, y = xy
    w_ = tw(d, s, font) + pad_x * 2
    h_ = font.size + pad_y * 2
    d.rounded_rectangle([x, y, x + w_, y + h_], radius=radius, fill=bg)
    d.text((x + pad_x, y + h_ / 2), s, font=font, fill=fg, anchor="lm")
    return x + w_, y + h_


def param_strip(d: ImageDraw.ImageDraw, y, items, x0: int | None = None,
                x1: int | None = None, font_val=None, font_lab=None,
                color_val=WHITE, color_lab=GRAY_D, color_accent=GOLD):
    """Нижняя строка характеристик: значение + подпись, разделители между колонками."""
    x0 = M if x0 is None else x0
    x1 = (W - M) if x1 is None else x1
    font_val = font_val or F(800, 46)
    font_lab = font_lab or F(600, 26)
    step = (x1 - x0) / len(items)
    for i, (val, lab, accent) in enumerate(items):
        cx = x0 + step * (i + 0.5)
        d.text((cx, y), val, font=font_val, fill=color_accent if accent else color_val,
               anchor="ma")
        d.text((cx, y + 68), lab, font=font_lab, fill=color_lab, anchor="ma")
        if i:
            hx = x0 + step * i
            d.line([hx, y + 6, hx, y + 96], fill=LINE, width=2)
    return y + 110


def brand_bar(img: Image.Image, chip_text: str = "OneLite Gold",
              logo_path: str | None = None, y: int = 84, chip_font=None):
    """Верхняя строка: чип линейки слева + логотип бренда справа."""
    d = ImageDraw.Draw(img)
    f = chip_font or F(800, 40)
    chip(d, (M, y), chip_text, f)
    if logo_path:
        lg = Image.open(logo_path).convert("RGBA")
        h = 108
        lg = lg.resize((int(lg.width * h / lg.height), h), Image.LANCZOS)
        img.alpha_composite(lg, (W - M - lg.width, y - 16))
    return y + 78
