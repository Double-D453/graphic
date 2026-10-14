"""Серия v02 — OneLite Gold, Ø 125 мм, P100, 8 отверстий.

Отличия от v01: на слайдах реальные фотографии товара, композиция ближе к
референсам пользователя (чип линейки + логотип бренда, стеклянные панели,
строка характеристик), схемы диска больше не используются.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import ds
from ds import (BG, GOLD, GOLD_D, GOLD_L, GRAY, GRAY_D, GRAPHITE, LINE, LINE_SOFT,
                PANEL, WHITE, F, divider, dim_line, dot, eyebrow, footer, h1, panel,
                para, text, tw, wrap, draw_tracked)
from ui2 import brand_bar, glass_panel, param_strip

W, H = ds.W, ds.H
M = 96
FOOT = 2268

LOGO = "/home/user/graphic/assets/logo/woodstock_logo_light.png"
AP = "/home/user/graphic/assets/product/"
P_FRONT = AP + "disc_front.png"
P_PAIR = AP + "disc_pair.png"
P_BOX = AP + "box_closed.png"
P_BOXOPEN = AP + "box_open.png"
P_MACRO = AP + "macro_surface.jpg"
P_BACK = AP + "macro_back.jpg"
P_HOLES = AP + "holes_closeup.jpg"
SCENE = "/home/user/graphic/assets/scenes/wood_before_after.jpg"

_cache: dict[str, Image.Image] = {}


def load(p: str) -> Image.Image:
    if p not in _cache:
        _cache[p] = Image.open(p).convert("RGBA")
    return _cache[p]


def place(base: Image.Image, path: str, x: float, y: float, w: float | None = None,
          h: float | None = None, shadow: bool = True, blur: int = 40,
          offset=(0, 24), alpha: int = 170) -> tuple[float, float]:
    """Накладывает фото с мягкой тенью. Возвращает (ширина, высота) результата."""
    im = load(path)
    if w:
        hh = int(im.height * w / im.width)
        im = im.resize((int(w), hh), Image.LANCZOS)
    elif h:
        ww = int(im.width * h / im.height)
        im = im.resize((ww, int(h)), Image.LANCZOS)
    x, y = int(x), int(y)
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        a = im.getchannel("A").point(lambda v: min(255, int(v * alpha / 255)))
        blk = Image.new("RGBA", im.size, (0, 0, 0, 255))
        blk.putalpha(a)
        sh.alpha_composite(blk, (x + offset[0], y + offset[1]))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(im, (x, y))
    return im.size


def photo_card(base: Image.Image, path: str, box, radius: int = 30, zoom: float = 1.0,
               css: str = "cover", border=(255, 255, 255, 70), width: int = 3,
               caption: str | None = None, caption_color=None, shadow: bool = True):
    """Фото внутри скруглённой рамки (как «стеклянные» фото-карточки в референсах)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    im = load(path).convert("RGB")
    tw_, th_ = x1 - x0, y1 - y0
    sc = max(tw_ / im.width, th_ / im.height) * zoom
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    left = (im.width - tw_) // 2
    top = int((im.height - th_) * 0.45)
    im = im.crop((left, top, left + tw_, top + th_)).convert("RGBA")

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sh.paste(Image.new("RGBA", (tw_, th_), (0, 0, 0, 190)), (x0, y0 + 20))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(34)))
    photo = Image.new("RGBA", base.size, (0, 0, 0, 0))
    photo.paste(im, (x0, y0))
    photo.putalpha(mask)
    base.alpha_composite(photo)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, outline=border, width=width)
    if caption:
        from ds import para as _para
        for i, line in enumerate(caption.split("\n")):
            _para(d, (x0 + 4, y1 + 22 + i * 44), line, F(500, 30),
                  caption_color or GRAY, tw_)
    return base


def glass_card(base: Image.Image, box, radius: int = 30, tint=(255, 255, 255, 16),
               border=(255, 255, 255, 62)):
    return glass_panel(base, box, radius=radius, tint=tint, border=border, blur=24)


def headline(d, y, kicker: str, title: str, sub: str | None = None,
             title_size: int = 104, kicker_color=GOLD) -> float:
    yy = eyebrow(d, y, kicker, kicker_color)
    yy = h1(d, yy - 8, title, size=title_size, max_w=W - 2 * M)
    if sub:
        d.text((M, yy + 6), sub, font=F(500, 42), fill=GRAY)
        yy += 62
    return yy


def page_no(d, n: int, total: int = 7):
    d.text((W - M, FOOT + 34), f"{n:02d} / {total:02d}", font=F(700, 28),
           fill=GRAY_D, anchor="ra")


def holes_of(path: str, cell: int = 8):
    """Центры светлых отверстий на вырезке диска (для аккуратных выносок)."""
    im = load(path)
    a = np.asarray(im)
    lum, al = a[..., :3].mean(2), a[..., 3]
    inside = al > 200
    cand = inside & (lum > np.percentile(lum[inside], 90))
    gh, gw = a.shape[0] // cell, a.shape[1] // cell
    grid = cand[:gh * cell, :gw * cell].reshape(gh, cell, gw, cell).mean((1, 3)) > 0.5
    seen, out = set(), []
    for y in range(gh):
        for x in range(gw):
            if grid[y, x] and (y, x) not in seen:
                st, pts = [(y, x)], []
                seen.add((y, x))
                while st:
                    cy, cx = st.pop()
                    pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < gh and 0 <= nx < gw and grid[ny, nx] and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            st.append((ny, nx))
                if 20 <= len(pts) <= 1200:
                    out.append((sum(p[1] for p in pts) / len(pts) * cell,
                                sum(p[0] for p in pts) / len(pts) * cell, len(pts)))
    return sorted(out, key=lambda b: -b[2])


# =====================================================================  S01
def s01() -> Image.Image:
    img = ds.make_bg(glow=(0.52, 0.60, 0.34, 46), vignette=0.62, seed=101)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 372, "ШЛИФОВАЛЬНЫЕ ДИСКИ")
    y = h1(d, y - 10, "ONELITE GOLD", size=146, max_w=1400)
    d.text((M, y + 10), "Для подготовки и промежуточной шлифовки древесины",
           font=F(500, 44), fill=GRAY)

    d = ImageDraw.Draw(img)
    cx, cy = W / 2, 1352
    d.ellipse([cx - 592, cy - 592, cx + 592, cy + 592], outline=GOLD + (58,), width=4)
    for i in range(8):                       # 8 меток по кругу — мотив перфорации
        ang = np.deg2rad(-90 + 22.5 + i * 45)
        mx, my = cx + 646 * np.cos(ang), cy + 646 * np.sin(ang)
        dot(d, mx, my, 9, GOLD + (170,))
    place(img, P_FRONT, cx - 596, cy - 596, w=1192, blur=52, alpha=185)

    d = ImageDraw.Draw(img)
    param_strip(d, 1990, [("125 мм", "ДИАМЕТР", False),
                          ("P100", "ЗЕРНИСТОСТЬ", True),
                          ("8", "ОТВЕРСТИЙ", False)],
                x0=M + 40, x1=W - M - 40)
    d.text((M, 2136), "Количество дисков в упаковке уточняйте в карточке товара.",
           font=F(600, 28), fill=GRAY_D)
    d.text((W - M, 2136), "На слайде — фотографии товара", font=F(600, 28),
           fill=GRAY_D, anchor="ra")
    footer(img, 1, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 1)
    return img


# =====================================================================  S02
def s02() -> Image.Image:
    img = ds.make_bg(glow=(0.16, 0.28, 0.34, 24), vignette=0.52, seed=102)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)
    headline(d, 296, "ПРИМЕНЕНИЕ", "Для чего подходит")

    photo_card(img, SCENE, (M, 664, M + 812, 1888), radius=30, zoom=1.05,
               caption="Иллюстрация: подготовка деревянной поверхности.\nНе фотография работы с этим диском.")
    d = ImageDraw.Draw(img)

    cards = [
        ("01", "Подготовка под отделку", "Выравнивание поверхности перед лаком, маслом или краской"),
        ("02", "Зашлифовка дефектов", "Неровности, поднятое волокно, следы прошлой обработки"),
        ("03", "Промежуточная шлифовка", "Обработка поверхности между слоями покрытия"),
    ]
    x0, x1 = 968, W - M
    yy = 664
    for num, title, body in cards:
        hgt = 372
        glass_card(img, [x0, yy, x1, yy + hgt])
        d = ImageDraw.Draw(img)
        d.text((x0 + 42, yy + 44), num, font=F(800, 40), fill=GOLD)
        d.text((x0 + 122, yy + 42), title, font=F(700, 40), fill=WHITE)
        para(d, (x0 + 122, yy + 116), body, F(500, 34), GRAY, x1 - x0 - 164)
        yy += hgt + 26

    d.text((M, 2136), "Зернистость P100 — середина шкалы: подходит для подготовки и "
                      "промежуточных этапов.", font=F(600, 28), fill=GRAY_D)
    footer(img, 2, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 2)
    return img


# =====================================================================  S03
def s03() -> Image.Image:
    img = ds.make_bg(glow=(0.22, 0.26, 0.32, 26), vignette=0.52, seed=103)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)
    headline(d, 296, "ЗЕРНИСТОСТЬ", "Зернистость P100",
             "Средняя ступень шкалы: между P80 и P120")

    d.text((M - 6, 700), "P100", font=F(800, 296), fill=GOLD)
    d.text((M + 8, 1054), "средняя ступень", font=F(700, 40), fill=(150, 120, 60))
    para(d, (M + 8, 1122), "Зерно средней величины: поверхность готовится быстрее, "
                           "чем мелким зерном, но след обработки заметнее, чем у P120 "
                           "и мельче.", F(500, 38), GRAY, 760)

    glass_card(img, [1040, 640, W - M, 1420])
    photo_card(img, P_MACRO, (1080, 680, W - M - 40, 1340), radius=24, zoom=1.0)
    d = ImageDraw.Draw(img)
    d.text((1080, 1362), "Рабочая сторона — макро", font=F(700, 36), fill=WHITE)
    d.text((1080, 1406), "Фотография абразивной поверхности", font=F(500, 30), fill=GRAY_D)

    sy = 1560
    draw_tracked(d, (M, sy), "ШКАЛА ЗЕРНИСТОСТИ — СПРАВОЧНО", F(800, 32), (150, 120, 60), 5.0)
    ax = sy + 224
    x0, x1 = M + 80, W - M - 80
    ticks = ["P60", "P80", "P100", "P120", "P150", "P180", "P240"]
    d.line([x0, ax, x1, ax], fill=LINE, width=3)
    step = (x1 - x0) / (len(ticks) - 1)
    for i, lab in enumerate(ticks):
        tx = x0 + i * step
        on = lab == "P100"
        d.line([tx, ax - 26, tx, ax + 26], fill=GOLD if on else LINE, width=5 if on else 3)
        d.text((tx, ax + 44), lab, font=F(800 if on else 600, 40 if on else 34),
               fill=GOLD if on else GRAY_D, anchor="ma")
    d.text((x0, ax - 92), "крупнее", font=F(600, 30), fill=GRAY_D)
    d.text((x1, ax - 92), "мельче", font=F(600, 30), fill=GRAY_D, anchor="ra")
    mx = x0 + ticks.index("P100") * step
    d.polygon([(mx, ax - 40), (mx - 19, ax - 72), (mx + 19, ax - 72)], fill=GOLD)

    d.text((M, 2060), "Шкала приведена справочно, как ориентир по зернистости. "
                      "В линейке OneLite Gold есть и другие значения.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 3, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 3)
    return img


# =====================================================================  S04
def s04() -> Image.Image:
    img = ds.make_bg(glow=(0.24, 0.42, 0.30, 26), vignette=0.52, seed=104)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)
    headline(d, 296, "КОНСТРУКЦИЯ", "8 отверстий",
             "Отверстия для отвода пыли из зоны шлифования")

    ph_w = 830
    ph_h = int(load(P_FRONT).height * ph_w / load(P_FRONT).width)
    px, py = M + 10, 800
    size = place(img, P_FRONT, px, py, w=ph_w, blur=44, alpha=185)
    d = ImageDraw.Draw(img)
    holes = holes_of(P_FRONT)
    k = ph_w / load(P_FRONT).width
    # выноска к верхнему левому отверстию
    hx, hy = px + holes[3][0] * k, py + holes[3][1] * k
    d.line([hx, hy, hx - 180, hy - 150], fill=GOLD_L, width=3)
    dot(d, hx, hy, 9, GOLD)
    d.line([M + 10, 700, hx - 176, hy - 146], fill=GOLD_L, width=3)
    d.text((M + 10, 664), "8 отверстий по кругу", font=F(700, 36), fill=GOLD_L)
    # размерная линия по диаметру
    dy = py + size[1] + 54
    xl, xr = px + 30, px + ph_w - 30
    d.line([xl, py + size[1] - 4, xl, dy + 30], fill=(90, 100, 104), width=2)
    d.line([xr, py + size[1] - 4, xr, dy + 30], fill=(90, 100, 104), width=2)
    dim_line(d, xl, dy, xr, dy, color=GOLD, width=3, cap=18)
    d.text((px + ph_w / 2, dy + 20), "Ø 125 мм", font=F(800, 40), fill=GOLD, anchor="ma")
    d.text((px + 4, dy + 108), "Фотография товара OneLite Gold", font=F(500, 30),
           fill=GRAY_D)

    x0, x1 = 1000, W - M
    glass_card(img, [x0, 664, x1, 1516])
    d = ImageDraw.Draw(img)
    d.text((x0 + 42, 706), "Как сверить с подошвой", font=F(700, 46), fill=WHITE)
    d.line([x0 + 42, 782, x1 - 42, 782], fill=LINE_SOFT, width=2)
    rows = [
        ("Число отверстий", "Посчитайте отверстия на подошве — должно совпасть: 8"),
        ("Рисунок отверстий", "Отверстия расположены по кругу — сверьте с фото"),
        ("Диаметр", "Диаметр диска — 125 мм, как и у подошвы"),
    ]
    yy = 820
    for title, body in rows:
        d.text((x0 + 42, yy), title, font=F(700, 40), fill=GOLD)
        para(d, (x0 + 42, yy + 56), body, F(500, 34), GRAY, x1 - x0 - 84)
        yy += 226

    glass_card(img, [x0, 1560, x1, 1900], tint=(255, 255, 255, 12))
    d = ImageDraw.Draw(img)
    d.text((x0 + 42, 1600), "Зачем отверстия", font=F(700, 42), fill=GOLD)
    para(d, (x0 + 42, 1672), "Пыль и мелкая стружка уходят из зоны шлифования "
                             "через отверстия диска и подошвы.",
         F(500, 34), WHITE, x1 - x0 - 84)

    d.text((M, 2136), "Отверстия видны на фотографии товара. Расположение — по окружности.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 4, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 4)
    return img


# =====================================================================  S05
def s05() -> Image.Image:
    img = ds.make_bg(glow=(0.58, 0.40, 0.30, 32), vignette=0.55, seed=105)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)
    headline(d, 296, "КРУПНЫЙ ПЛАН", "Что видно вблизи",
             "Обе стороны диска на реальных снимках")

    photo_card(img, P_BACK, (M, 700, M + 830, 1220), radius=28, zoom=1.02,
               caption="Обратная сторона: ворсистая подложка и печать зернистости")
    photo_card(img, P_MACRO, (M, 1420, M + 830, 1950), radius=28, zoom=1.0,
               caption="Рабочая сторона: абразивное зерно крупным планом")

    x0, x1 = 1000, W - M
    glass_card(img, [x0, 700, x1, 1240])
    d = ImageDraw.Draw(img)
    d.text((x0 + 42, 742), "Подложка", font=F(700, 46), fill=GOLD)
    para(d, (x0 + 42, 818), "На обратной стороне — ворсистая (велкро) подложка: диск "
                            "крепится на подошву с ответной частью и снимается без "
                            "инструмента.", F(500, 38), WHITE, x1 - x0 - 84)
    d.text((x0 + 42, 1060), "Маркировка P100 напечатана на подложке",
           font=F(500, 32), fill=GRAY)

    glass_card(img, [x0, 1280, x1, 1800], tint=(255, 255, 255, 12))
    d = ImageDraw.Draw(img)
    d.text((x0 + 42, 1322), "Абразивный слой", font=F(700, 46), fill=GOLD)
    para(d, (x0 + 42, 1398), "Рабочая сторона — зерно на жёлтой основе. На макро "
                             "видно отдельные зерна и распределение по поверхности.",
         F(500, 38), WHITE, x1 - x0 - 84)
    d.line([x0 + 42, 1626, x1 - 42, 1626], fill=LINE_SOFT, width=2)
    d.text((x0 + 42, 1662), "Крупные планы сделаны с фото товара,", font=F(500, 32), fill=GRAY)
    d.text((x0 + 42, 1704), "без дорисовки поверхности.", font=F(500, 32), fill=GRAY)

    d = ImageDraw.Draw(img)
    param_strip(d, 2030, [("Ø 125 мм", "ДИАМЕТР", False), ("P100", "ЗЕРНИСТОСТЬ", True),
                          ("8", "ОТВЕРСТИЙ", False)],
                x0=M + 40, x1=W - M - 40, font_val=F(700, 42))
    footer(img, 5, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 5)
    return img


# =====================================================================  S06
def s06() -> Image.Image:
    img = ds.make_bg(glow=(0.20, 0.36, 0.30, 24), vignette=0.52, seed=106)
    brand_bar(img, "OneLite Gold", LOGO)
    d = ImageDraw.Draw(img)
    headline(d, 296, "РАЗМЕР И УПАКОВКА", "Ø 125 мм", "Сверьте диаметр подошвы шлифмашинки")

    bw = 470
    place(img, P_BOX, M + 30, 700, w=bw, blur=40, alpha=165)
    bh = int(load(P_BOX).height * bw / load(P_BOX).width)
    d = ImageDraw.Draw(img)
    d.text((M, 700 + bh + 44), "Упаковка OneLite", font=F(700, 38), fill=WHITE)
    d.text((M, 700 + bh + 96), "Количество дисков в упаковке", font=F(500, 32), fill=GRAY_D)
    d.text((M, 700 + bh + 138), "уточняйте в карточке товара.", font=F(500, 32), fill=GRAY_D)

    ow = 560
    place(img, P_BOXOPEN, 610, 700, w=ow, blur=40, alpha=150)
    oh = int(load(P_BOXOPEN).height * ow / load(P_BOXOPEN).width)
    d = ImageDraw.Draw(img)
    d.text((610, 700 + oh + 44), "Открытая упаковка", font=F(700, 38), fill=WHITE)

    x0, x1 = 1250, W - M
    glass_card(img, [x0, 664, x1, 1424])
    d = ImageDraw.Draw(img)
    d.text((x0 + 38, 706), "Что учесть", font=F(800, 46), fill=GOLD)
    d.line([x0 + 38, 784, x1 - 38, 784], fill=LINE_SOFT, width=2)
    rows = [
        ("Диаметр", "Диск 125 мм рассчитан на подошву такого же диаметра"),
        ("Форма", "Проверьте число и рисунок отверстий на подошве"),
        ("Зернистость", "В линейке есть другие значения — выберите под задачу"),
    ]
    yy = 820
    for title, body in rows:
        d.text((x0 + 38, yy), title, font=F(700, 38), fill=WHITE)
        para(d, (x0 + 38, yy + 54), body, F(500, 32), GRAY, x1 - x0 - 76)
        yy += 196

    d.text((M, 1700), "Перед покупкой", font=F(700, 44), fill=WHITE)
    d.text((M, 1768), "Измерьте подошву и посчитайте отверстия —", font=F(500, 36), fill=GRAY)
    d.text((M, 1818), "так диск точно подойдёт.", font=F(500, 36), fill=GRAY)

    d.text((M, 2136), "На слайдах — фотографии товара OneLite Gold.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 6, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 6)
    return img


# =====================================================================  S07
def s07() -> Image.Image:
    img = ds.make_bg(glow=(0.5, 0.34, 0.32, 40), vignette=0.6, seed=107)
    lg = load(LOGO)
    h = 268
    lg = lg.resize((int(lg.width * h / lg.height), h), Image.LANCZOS)
    img.alpha_composite(lg, ((W - lg.width) // 2, 190))
    d = ImageDraw.Draw(img)

    d.text((W / 2, 520), "ШЛИФОВАЛЬНЫЕ ДИСКИ", font=F(800, 34), fill=GOLD, anchor="ma")
    d.text((W / 2, 590), "ONELITE GOLD", font=F(800, 118), fill=WHITE, anchor="ma")
    d.text((W / 2, 750), "P100 · Ø 125 мм · 8 отверстий", font=F(600, 50), fill=GOLD_L,
           anchor="ma")

    cards = [("Ø 125 мм", "подходит под такую же подошву"),
             ("8 отверстий", "по кругу — сверьте с подошвой"),
             ("P100", "подготовка и промежуточная шлифовка"),
             ("Линейка", "есть и другие значения зернистости")]
    cw, ch, gap = 762, 214, 32
    x0 = (W - (cw * 2 + gap)) / 2
    for i, (title, body) in enumerate(cards):
        cx = x0 + (i % 2) * (cw + gap)
        cy = 880 + (i // 2) * (ch + gap)
        glass_card(img, [cx, cy, cx + cw, cy + ch], tint=(255, 255, 255, 16))
        d = ImageDraw.Draw(img)
        d.text((cx + 42, cy + 44), title, font=F(800, 48), fill=GOLD if i in (0, 2) else WHITE)
        d.text((cx + 42, cy + 118), body, font=F(500, 34), fill=GRAY)

    place(img, P_PAIR, (W - 1010) / 2, 1370, w=1010, blur=46, alpha=165)

    d.text((W / 2, 2076), "Перед заказом сверьте параметры со своей шлифмашинкой.",
           font=F(600, 36), fill=GRAY, anchor="ma")
    d.text((W / 2, 2132), "Фотографии товара OneLite Gold.", font=F(600, 28),
           fill=GRAY_D, anchor="ma")
    footer(img, 7, left="OneLite Gold · P100 · Ø 125 мм · 8 отверстий")
    page_no(d, 7)
    return img
