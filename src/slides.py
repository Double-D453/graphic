"""Семь слайдов серии OneLite Gold P100 Ø125 мм 8 отверстий (1792 x 2400)."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import ds
from ds import (BG, GOLD, GOLD_D, GOLD_L, GRAY, GRAY_D, GRAPHITE, LINE, LINE_SOFT,
                M, H, W, PANEL, PANEL_2, WHITE, F, divider, dot, eyebrow, footer,
                h1, header, panel, para, paste_shadow, text, tw, wrap, draw_tracked,
                bullet, chip, chip_outline, dim_line, gold_rule, number_badge)
from disc import disc_perspective, disc_render, disc_scheme, grain_swatch

LOGO = "/home/user/graphic/assets/logo/woodstock_logo_light.png"
SCENE_APPLY = "/home/user/graphic/assets/scenes/wood_before_after.jpg"
SCENE_MACRO = "/home/user/graphic/assets/scenes/wood_macro.jpg"
NOTE_SCHEME = "Условная схема. Не фотография товара"

_logo_cache: dict[int, Image.Image] = {}


def logo(height: int) -> Image.Image:
    if height not in _logo_cache:
        im = Image.open(LOGO).convert("RGBA")
        w = int(im.width * height / im.height)
        _logo_cache[height] = im.resize((w, height), Image.LANCZOS)
    return _logo_cache[height]


def place_scene(base: Image.Image, path: str, y0: int, height: int,
                fade_top: int = 300, fade_bottom: int = 300,
                darken: float = 0.42, warm: float = 0.03, anchor_y: float = 0.5):
    """Кадр-иллюстрация во всю ширину с растворением в фон сверху/снизу."""
    im = Image.open(path).convert("RGB")
    scale = max(W / im.width, height / im.height)
    im = im.resize((max(W, int(im.width * scale)), max(height, int(im.height * scale))),
                   Image.LANCZOS)
    left = (im.width - W) // 2
    top = int((im.height - height) * anchor_y)
    im = im.crop((left, top, left + W, top + height))

    arr = np.asarray(im).astype(np.float32) * (1 - darken)
    arr[..., 0] *= (1 + warm)
    arr[..., 2] *= (1 - warm)
    h = arr.shape[0]
    idx = np.arange(h, dtype=np.float32)
    a = np.minimum(np.clip(idx / max(1, fade_top), 0, 1),
                   np.clip((h - idx) / max(1, fade_bottom), 0, 1)) ** 1.05
    a = np.repeat(a[:, None], W, axis=1)
    sprite = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    sprite.putalpha(Image.fromarray((a * 255).astype(np.uint8), "L"))
    base.alpha_composite(sprite, (0, y0))
    return base


# =====================================================================  S01
def s01_cover() -> Image.Image:
    img = ds.make_bg(glow=(0.58, 0.66, 0.30, 62), vignette=0.62, seed=21)
    d = ImageDraw.Draw(img)

    # декоративные окружности за диском
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    cx, cy = 1010, 1580
    dl.ellipse([cx - 600, cy - 600, cx + 600, cy + 600], outline=GOLD + (46,), width=3)
    dl.ellipse([cx - 680, cy - 680, cx + 680, cy + 680], outline=LINE + (90,), width=2)
    for i in range(8):                      # 8 меток по кругу — мотив отверстий
        ang = np.deg2rad(-90 + 22.5 + i * 45)
        px, py = cx + 640 * np.cos(ang), cy + 640 * np.sin(ang)
        dl.ellipse([px - 7, py - 7, px + 7, py + 7], fill=GOLD + (150,))
    img.alpha_composite(lay)

    hero = disc_render(1040, holes=8, seed=13)
    paste_shadow(img, hero, (cx - hero.width // 2, cy - hero.height // 2),
                 blur=48, offset=(0, 26), alpha=185)

    lg = logo(118)
    img.alpha_composite(lg, (M, 106))
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 400, "ШЛИФОВАЛЬНЫЙ ДИСК")
    y = h1(d, y - 8, "OneLite Gold", size=152, max_w=1450)
    d.text((M, y + 6), "Зернистость P100 · Ø 125 мм · 8 отверстий",
           font=F(500, 50), fill=GRAY)

    x = M
    for label in ("P100", "Ø 125 мм", "8 отверстий"):
        x, _ = chip(d, (x, 830), label, F(700, 44), fg=GOLD_L,
                    bg=(32, 26, 13), border=(104, 78, 26), pad_x=38, pad_y=24)
        x += 28

    d.text((W / 2, 2135), "Схематичное изображение диска — не фотография товара",
           font=F(600, 30), fill=GRAY_D, anchor="ma")
    footer(img, 1, right="Обложка")
    return img


# =====================================================================  S02
def s02_apply() -> Image.Image:
    img = ds.make_bg(glow=(0.20, 0.22, 0.34, 26), vignette=0.5, seed=31)
    header(img, 2)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 300, "ПРИМЕНЕНИЕ")
    y = h1(d, y - 6, "Подготовка древесины", size=104)
    d.text((M, y + 8), "Типовые задачи, где применяют среднюю зернистость",
           font=F(500, 44), fill=GRAY)

    items = [
        ("01", "Подготовка под отделку",
         "Выравнивание поверхности перед лаком, маслом или краской"),
        ("02", "Зашлифовка дефектов",
         "Неровности, поднятое волокно, следы прошлой обработки"),
        ("03", "Промежуточная шлифовка",
         "Обработка поверхности между слоями покрытия"),
    ]
    yy = 660
    for num, title, desc in items:
        number_badge(img, M + 48, yy + 44, num, r=46, font=F(800, 44))
        d = ImageDraw.Draw(img)
        d.text((M + 126, yy), title, font=F(700, 50), fill=WHITE)
        d.text((M + 126, yy + 66), desc, font=F(500, 38), fill=GRAY)
        yy += 166

    img = place_scene(img, SCENE_APPLY, 1180, 1030, fade_top=300, fade_bottom=330,
                      darken=0.34, anchor_y=0.42)
    d = ImageDraw.Draw(img)
    d.text((M, 2205), "Иллюстрация процесса шлифования. Не фотография конкретного экземпляра товара.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 2)
    return img


# =====================================================================  S03
def s03_grit() -> Image.Image:
    img = ds.make_bg(glow=(0.26, 0.30, 0.32, 24), vignette=0.5, seed=41)
    header(img, 3)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 300, "ЗЕРНИСТОСТЬ")
    y = h1(d, y - 6, "Зернистость P100", size=104)
    d.text((M, y + 8), "Средняя ступень шкалы: между P80 и P120",
           font=F(500, 44), fill=GRAY)

    # крупный номер
    d.text((M - 6, 660), "P100", font=F(800, 300), fill=GOLD)
    d.text((M + 6, 990), "средняя ступень", font=F(700, 40), fill=(150, 120, 60))

    # пояснения справа
    bx = 1010
    d.text((bx, 690), "Зерно средней величины", font=F(700, 46), fill=WHITE)
    para(d, (bx, 760), "Подходит для подготовки поверхности и промежуточных "
                       "этапов шлифовки дерева.", F(500, 38), GRAY, W - M - bx)
    d.line([bx, 900, W - M, 900], fill=LINE_SOFT, width=2)
    d.text((bx, 930), "Мельче P80 · грубее P120", font=F(600, 36), fill=GOLD_L)

    # шкала зернистости
    sy = 1250
    draw_tracked(d, (M, sy), "ШКАЛА ЗЕРНИСТОСТИ — СПРАВОЧНО", F(800, 32), (150, 120, 60), 5.0)
    axis_y = sy + 250
    x0, x1 = M + 90, W - M - 90
    ticks = ["P60", "P80", "P100", "P120", "P150", "P180", "P240"]
    d.line([x0, axis_y, x1, axis_y], fill=LINE, width=3)
    step = (x1 - x0) / (len(ticks) - 1)
    for i, label in enumerate(ticks):
        tx = x0 + i * step
        active = label == "P100"
        d.line([tx, axis_y - 26, tx, axis_y + 26], fill=GOLD if active else LINE,
               width=5 if active else 3)
        d.text((tx, axis_y + 44), label, font=F(800 if active else 600, 40 if active else 34),
               fill=GOLD if active else GRAY_D, anchor="ma")
    d.text((x0, axis_y - 96), "крупнее", font=F(600, 32), fill=GRAY_D)
    d.text((x1, axis_y - 96), "мельче", font=F(600, 32), fill=GRAY_D, anchor="ra")
    idx = ticks.index("P100")
    mx = x0 + idx * step
    d.polygon([(mx, axis_y - 40), (mx - 20, axis_y - 74), (mx + 20, axis_y - 74)], fill=GOLD)

    # три колонки-пояснения
    top = 1700
    cw = (W - 2 * M - 2 * 32) / 3
    cols = [
        ("Крупнее зерно", "Быстрее снимает материал,\nно оставляет более заметные риски", False),
        ("Зерно P100", "Средний вариант: подготовка\nи промежуточная шлифовка", True),
        ("Мельче зерно", "Ровнее след обработки,\nно снимает медленнее", False),
    ]
    for i, (title, body, hi) in enumerate(cols):
        x = M + i * (cw + 32)
        panel(img, [x, top, x + cw, top + 300], radius=28,
              fill=PANEL_2 if hi else PANEL,
              outline=(96, 74, 28) if hi else LINE_SOFT, width=3 if hi else 2)
        d = ImageDraw.Draw(img)
        d.text((x + 40, top + 46), title, font=F(800, 46), fill=GOLD if hi else WHITE)
        para(d, (x + 40, top + 130), body.replace("\n", " "), F(500, 38), GRAY, cw - 80)

    d = ImageDraw.Draw(img)
    d.text((M, 2090), "Шкала и пояснения приведены справочно, как общий ориентир по зернистости.",
           font=F(600, 28), fill=GRAY_D)
    d.text((M, 2140), "В линейке OneLite Gold — разные значения зернистости.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 3)
    return img


# =====================================================================  S04
def s04_holes() -> Image.Image:
    img = ds.make_bg(glow=(0.30, 0.50, 0.30, 26), vignette=0.5, seed=51)
    header(img, 4)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 300, "КОНСТРУКЦИЯ")
    y = h1(d, y - 6, "8 отверстий", size=104)
    d.text((M, y + 8), "Отвод пыли при шлифовке", font=F(500, 44), fill=GRAY)

    # схема диска + размер
    SZ = 720
    sch = disc_scheme(SZ, holes=8, fill=(20, 26, 28, 255))
    sx, sy = 130, 810
    img.alpha_composite(sch, (sx, sy))
    d = ImageDraw.Draw(img)
    ccx, ccy = sx + sch.width / 2, sy + sch.height / 2
    # выноска на отверстие (верхне-левая четверть диска)
    hx = ccx + 0.60 * (SZ / 2) * np.cos(np.deg2rad(202.5))
    hy = ccy + 0.60 * (SZ / 2) * np.sin(np.deg2rad(202.5))
    chip_x, chip_y = M + 10, 636
    chip_r, chip_b = chip(d, (chip_x, chip_y), "8 отверстий по кругу", F(700, 34), fg=GOLD_L,
                          bg=(32, 26, 13), border=(104, 78, 26), pad_x=24, pad_y=14)
    d.line([(chip_x + chip_r) / 2, chip_b, hx - 6, hy - 10], fill=GOLD_L, width=3)
    d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=GOLD)
    # размерная линия снизу
    dy = sy + SZ + 56
    xl, xr = sx + 26, sx + SZ - 26
    d.line([xl, sy + SZ, xl, dy + 26], fill=(90, 100, 104), width=2)
    d.line([xr, sy + SZ, xr, dy + 26], fill=(90, 100, 104), width=2)
    dim_line(d, xl, dy, xr, dy, color=GOLD, width=3, cap=20)
    d.text(((xl + xr) / 2, dy + 18), "Ø 125 мм", font=F(800, 40), fill=GOLD, anchor="ma")
    d.text((ccx, sy - 62), "вид сверху", font=F(600, 32), fill=GRAY_D, anchor="ma")

    # чек-лист справа
    bx = 960
    bw = W - M - bx
    d.text((bx, 810), "Как сверить со своей тарелкой", font=F(700, 48), fill=WHITE)
    d.line([bx, 896, W - M, 896], fill=LINE_SOFT, width=2)
    checks = [
        ("01", "Число отверстий", "Посчитайте отверстия на подошве шлифмашинки — их должно быть 8"),
        ("02", "Диаметр", "Измерьте подошву: диаметр диска — 125 мм"),
        ("03", "Рисунок отверстий", "Отверстия идут по кругу — сверьте с фото товара"),
    ]
    yy = 936
    for num, title, desc in checks:
        d.text((bx, yy - 4), num, font=F(800, 38), fill=GOLD)
        d.text((bx + 94, yy - 8), title, font=F(700, 42), fill=WHITE)
        para(d, (bx, yy + 54), desc, F(500, 34), GRAY, bw)
        yy += 186
        if num != "03":
            d.line([bx, yy - 66, W - M, yy - 66], fill=LINE_SOFT, width=2)

    # назначение отверстий
    py = 1660
    panel(img, [M, py, W - M, py + 400], radius=30, fill=PANEL, outline=LINE_SOFT)
    d = ImageDraw.Draw(img)
    d.text((M + 50, py + 46), "Зачем нужны отверстия", font=F(800, 48), fill=GOLD)
    bullet(d, M + 52, py + 140, "Отвод пыли и мелкой стружки из зоны шлифования при работе",
           F(500, 38), WHITE, gap=30, max_w=W - 2 * M - 140)
    bullet(d, M + 52, py + 244, "Работают в паре с перфорацией подошвы шлифмашинки — сверяйте рисунок",
           F(500, 38), WHITE, gap=30, max_w=W - 2 * M - 140)

    d.text((M, 2145), "Схема условная: расположение отверстий сверяйте с фотографиями в карточке товара.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 4)
    return img


# =====================================================================  S05
def s05_closeup() -> Image.Image:
    img = ds.make_bg(glow=(0.64, 0.42, 0.30, 34), vignette=0.55, seed=61)
    header(img, 5)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 300, "КРУПНЫЙ ПЛАН")
    y = h1(d, y - 6, "Рабочая сторона", size=104)
    d.text((M, y + 8), "Что видно на увеличенном фрагменте",
           font=F(500, 44), fill=GRAY)

    # диск в перспективе
    persp = disc_perspective(1120, holes=8, tilt=0.45, seed=17)
    px, py = 110, 870
    paste_shadow(img, persp, (px, py), blur=44, offset=(0, 26), alpha=170)
    d = ImageDraw.Draw(img)
    ccx, ccy = px + persp.width / 2, py + persp.height / 2
    # выноска на отверстие (правая верхняя четверть диска)
    hx = ccx + 0.60 * (persp.width / 2) * np.cos(np.deg2rad(-45))
    hy = ccy + 0.45 * 0.60 * (persp.width / 2) * np.sin(np.deg2rad(-45))
    d.line([hx, hy, hx + 130, hy - 96], fill=GOLD_L, width=3)
    d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=GOLD)
    chip(d, (hx + 140, hy - 150), "8 отверстий по кругу", F(700, 34), fg=GOLD_L,
         bg=(32, 26, 13), border=(104, 78, 26), pad_x=24, pad_y=14)
    # выноска на зернистость (левый нижний край)
    gx = ccx - 0.82 * (persp.width / 2) * np.cos(np.deg2rad(28))
    gy = ccy + 0.45 * 0.82 * (persp.width / 2) * np.sin(np.deg2rad(28))
    d.line([gx, gy, gx - 150, gy + 130], fill=GOLD_L, width=3)
    d.ellipse([gx - 8, gy - 8, gx + 8, gy + 8], fill=GOLD)
    chip(d, (M + 20, gy + 120), "Зерно P100", F(700, 34), fg=GOLD_L, bg=(32, 26, 13),
         border=(104, 78, 26), pad_x=24, pad_y=14)

    # врезка: условная структура абразивного слоя
    T = 520
    tex = grain_swatch(T, density=0.30, grain_px=2.4, seed=9)
    tx, ty = 1180, 1090
    img.alpha_composite(tex, (tx, ty))
    d = ImageDraw.Draw(img)
    tcx, tcy = tx + T / 2, ty + T / 2
    d.ellipse([tx, ty, tx + T, ty + T], outline=(150, 130, 70), width=3)
    d.line([gx, gy, tx + T * 0.18, ty + T * 0.92], fill=(120, 104, 60), width=2)
    para(d, (tx, ty + T + 40), "Условная структура абразивного слоя", F(700, 34),
         WHITE, W - M - tx, leading=1.18)
    para(d, (tx, ty + T + 138), "Схематично, при увеличении. Точный вид поверхности — "
                                "на фото товара.", F(500, 32), GRAY, W - M - tx)

    # нижняя линия спецификаций
    d.line([M, 1960, W - M, 1960], fill=LINE_SOFT, width=2)
    d.text((M, 2000), "Ø 125 мм", font=F(800, 54), fill=GOLD)
    d.text((M, 2072), "диаметр рабочей поверхности", font=F(500, 33), fill=GRAY_D)
    d.text((W / 2, 2000), "P100", font=F(800, 54), fill=GOLD, anchor="ma")
    d.text((W / 2, 2072), "зернистость", font=F(500, 33), fill=GRAY_D, anchor="ma")
    d.text((W - M, 2000), "8 отверстий", font=F(800, 54), fill=GOLD, anchor="ra")
    d.text((W - M, 2072), "по кругу", font=F(500, 33), fill=GRAY_D, anchor="ra")

    d.text((M, 2185), NOTE_SCHEME, font=F(600, 28), fill=GRAY_D)
    footer(img, 5)
    return img


# =====================================================================  S06
def s06_size() -> Image.Image:
    img = ds.make_bg(glow=(0.26, 0.42, 0.30, 24), vignette=0.5, seed=71)
    header(img, 6)
    d = ImageDraw.Draw(img)

    y = eyebrow(d, 300, "РАЗМЕР")
    y = h1(d, y - 6, "Ø 125 мм", size=104)
    d.text((M, y + 8), "Сверьте диаметр подошвы шлифмашинки",
           font=F(500, 44), fill=GRAY)

    # схема: диск + размер
    sch = disc_scheme(660, holes=8, fill=(20, 26, 28, 255))
    sx, sy = 170, 830
    img.alpha_composite(sch, (sx, sy))
    d = ImageDraw.Draw(img)
    cx, cy = sx + sch.width / 2, sy + sch.height / 2
    d.ellipse([cx - 400, cy - 400, cx + 400, cy + 400], outline=LINE + (200,), width=3)
    d.text((cx, cy - 400 - 56), "подошва (тарелка) 125 мм", font=F(600, 32), fill=GRAY_D,
           anchor="ma")
    dy = sy + sch.height + 80
    xl, xr = sx + 20, sx + sch.width - 20
    d.line([xl, sy + sch.height, xl, dy + 26], fill=(90, 100, 104), width=2)
    d.line([xr, sy + sch.height, xr, dy + 26], fill=(90, 100, 104), width=2)
    dim_line(d, xl, dy, xr, dy, color=GOLD, width=3, cap=20)
    d.text(((xl + xr) / 2, dy + 16), "Ø 125 мм", font=F(800, 40), fill=GOLD, anchor="ma")

    # что учесть
    bx = 1020
    bw = W - M - bx
    panel(img, [bx - 46, 810, W - M, 1620], radius=30, fill=PANEL, outline=LINE_SOFT)
    d = ImageDraw.Draw(img)
    d.text((bx, 864), "Что учесть", font=F(800, 52), fill=GOLD)
    d.line([bx, 956, W - M - 20, 956], fill=LINE_SOFT, width=2)
    rows = [
        ("Диаметр", "Диск 125 мм рассчитан на подошву такого же диаметра"),
        ("Форма", "Проверьте число и рисунок отверстий на подошве шлифмашинки"),
        ("Зернистость", "В линейке OneLite Gold есть разные значения — выберите под задачу"),
    ]
    yy = 992
    for title, body in rows:
        d.text((bx, yy), title, font=F(700, 42), fill=WHITE)
        para(d, (bx, yy + 56), body, F(500, 34), GRAY, bw)
        yy += 200

    d.text((M, 1740), "Перед покупкой", font=F(700, 44), fill=WHITE)
    d.text((M, 1806), "Измерьте подошву и посчитайте отверстия — так диск точно подойдёт.",
           font=F(500, 36), fill=GRAY)
    d.text((M, 1885), "Количество дисков в упаковке уточняйте в карточке товара.",
           font=F(600, 28), fill=GRAY_D)
    d.text((M, 1945), NOTE_SCHEME + ". Габарит показан условно.",
           font=F(600, 28), fill=GRAY_D)
    footer(img, 6)
    return img


# =====================================================================  S07
def s07_final() -> Image.Image:
    img = ds.make_bg(glow=(0.50, 0.34, 0.34, 40), vignette=0.6, seed=81)
    d = ImageDraw.Draw(img)

    lg = logo(300)
    img.alpha_composite(lg, ((W - lg.width) // 2, 300))
    d = ImageDraw.Draw(img)

    d.text((W / 2, 760), "ШЛИФОВАЛЬНЫЙ ДИСК", font=F(800, 34), fill=GOLD, anchor="ma")
    d.text((W / 2, 830), "OneLite Gold", font=F(800, 132), fill=WHITE, anchor="ma")
    d.text((W / 2, 1010), "P100 · Ø 125 мм · 8 отверстий", font=F(600, 54), fill=GOLD_L,
           anchor="ma")

    gold_rule(d, W / 2 - 150, 1130, 300, h=6)

    d.text((W / 2, 1240), "Памятка по выбору", font=F(800, 46), fill=WHITE, anchor="ma")
    cards = [
        ("Ø 125 мм", "диаметр подошвы шлифмашинки"),
        ("8 отверстий", "по кругу — сверьте с подошвой"),
        ("P100", "подготовка и промежуточная шлифовка"),
        ("Линейка", "есть и другие значения зернистости"),
    ]
    cw, ch, gap = 720, 200, 40
    x0 = (W - (cw * 2 + gap)) / 2
    for i, (title, body) in enumerate(cards):
        cx = x0 + (i % 2) * (cw + gap)
        cy = 1340 + (i // 2) * (ch + gap)
        hi = i in (0, 2)
        panel(img, [cx, cy, cx + cw, cy + ch], radius=28,
              fill=PANEL_2 if hi else PANEL,
              outline=(96, 74, 28) if hi else LINE_SOFT, width=3 if hi else 2)
        d = ImageDraw.Draw(img)
        d.text((cx + 44, cy + 42), title, font=F(800, 50), fill=GOLD if hi else WHITE)
        d.text((cx + 44, cy + 116), body, font=F(500, 34), fill=GRAY)

    d = ImageDraw.Draw(img)
    d.text((W / 2, 1870), "Перед заказом сверьте параметры со своей шлифмашинкой.",
           font=F(600, 36), fill=GRAY, anchor="ma")
    d.text((W / 2, 1930), NOTE_SCHEME + ".", font=F(600, 28), fill=GRAY_D, anchor="ma")
    footer(img, 7, right="Финал серии")
    return img
