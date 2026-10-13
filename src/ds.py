"""OneLite Gold — дизайн-система для инфографики Ozon (1792 x 2400).

Все цвета/шрифты/примитивы серии в одном месте, чтобы 7 слайдов выглядели одной серией.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------- размеры
W, H = 1792, 2400
M = 120                     # боковое поле
FOOT_Y = H - 132            # линия футера
TOP_BAR_Y = 118

# ---------------------------------------------------------------- палитра
# Золото и графит взяты из фирменных файлов WOODSTOCK (ЛОГО/Woodstock_logo*).
BG        = (12, 17, 18)        # #0C1112 фирменный графит
BG_DEEP   = (8, 11, 12)
PANEL     = (20, 26, 28)
PANEL_2   = (26, 33, 36)
LINE      = (46, 55, 59)
LINE_SOFT = (34, 41, 44)
GOLD      = (247, 184, 55)      # #F7B837 фирменное золото
GOLD_L    = (255, 214, 130)
GOLD_D    = (168, 116, 26)
WHITE     = (255, 255, 255)
GRAY      = (158, 168, 172)
GRAY_D    = (112, 122, 126)
GRAPHITE  = (12, 17, 18)

FONT_DIR = "/home/user/graphic/assets/fonts"
_font_cache: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}


def F(weight: int, size: int) -> ImageFont.FreeTypeFont:
    """Шрифт Manrope нужного веса (200..800), с кириллицей."""
    key = (weight, size)
    f = _font_cache.get(key)
    if f is None:
        f = ImageFont.truetype(f"{FONT_DIR}/Manrope-{weight}.ttf", size)
        _font_cache[key] = f
    return f


# ---------------------------------------------------------------- фон
def _noise(shape, sigma, seed):
    rng = np.random.default_rng(seed)
    return rng.normal(0, sigma, shape)


def make_bg(glow: tuple[float, float, float, float] | None = None,
            glow_color=GOLD, vignette: float = 0.55, grain: float = 3.2,
            seed: int = 11,
            extra_glows: list[tuple[float, float, float, float]] | None = None) -> Image.Image:
    """Тёмный фон: вертикальный градиент + тёплое свечение + виньетка + зерно.

    glow = (cx, cy, radius, strength) в долях от размера холста.
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (yy / H)                                    # 0..1 сверху вниз
    base = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        base[..., i] = BG[i] * (1 - t * 0.35) + BG_DEEP[i] * (t * 0.35)

    def add_glow(cx, cy, radius, strength, color):
        """strength — максимальная прибавка яркости (в единицах 0..255)."""
        r = np.sqrt((xx - cx * W) ** 2 + (yy - cy * H) ** 2) / (radius * H)
        g = np.clip(1.0 - r, 0.0, 1.0) ** 2.6 * (strength / 255.0)
        for i in range(3):
            base[..., i] += color[i] * g

    if glow:
        add_glow(*glow, color=glow_color)
    for g in (extra_glows or []):
        add_glow(*g, color=glow_color)

    if vignette:
        cx, cy = W / 2, H * 0.46
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (0.72 * H)
        v = np.clip(r - 0.35, 0, 1) ** 1.6 * vignette
        base *= (1 - v)[..., None]

    if grain:
        base += _noise((H, W, 1), grain, seed)

    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    return img


def grain_overlay(img: Image.Image, strength: float = 5.0, seed: int = 3) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    a += _noise((H, W, 1), strength, seed)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ---------------------------------------------------------------- текст
def tw(d: ImageDraw.ImageDraw, s: str, font, tracking: float = 0.0) -> float:
    """Ширина строки с учётом трекинга."""
    if not tracking:
        return d.textlength(s, font=font)
    return sum(d.textlength(ch, font=font) for ch in s) + tracking * max(0, len(s) - 1)


def draw_tracked(d: ImageDraw.ImageDraw, xy, s: str, font, fill, tracking=0.0, anchor_y="la"):
    """Текст с трекингом (по буквам). xy — левый верх (или по anchor_y)."""
    x, y = xy
    if not tracking:
        d.text((x, y), s, font=font, fill=fill, anchor=anchor_y)
        return
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill, anchor=anchor_y)
        x += d.textlength(ch, font=font) + tracking


def text(d, xy, s, font, fill, anchor="la", tracking=0.0):
    if tracking:
        draw_tracked(d, xy, s, font, fill, tracking, anchor)
    else:
        d.text(xy, s, font=font, fill=fill, anchor=anchor)


def wrap(d: ImageDraw.ImageDraw, s: str, font, max_w: float, tracking=0.0) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        probe = (cur + " " + w_).strip()
        if tw(d, probe, font, tracking) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def para(d, xy, s, font, fill, max_w, leading=1.28, tracking=0.0):
    x, y = xy
    lh = font.size * leading
    for i, line in enumerate(wrap(d, s, font, max_w, tracking)):
        d.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(wrap(d, s, font, max_w, tracking)) * lh


# ---------------------------------------------------------------- элементы
def chip(d, xy, s, font, fg=GOLD, bg=(30, 25, 12),
         border=(92, 70, 24), pad_x=34, pad_y=20, radius=18, tracking=0.0):
    """Плашка-чип. xy — левый верх. Возвращает (right, bottom)."""
    x, y = xy
    w_ = tw(d, s, font, tracking) + pad_x * 2
    h_ = font.size + pad_y * 2
    d.rounded_rectangle([x, y, x + w_, y + h_], radius=radius, fill=bg,
                        outline=border, width=2)
    text(d, (x + pad_x, y + h_ / 2), s, font, fg, anchor="lm", tracking=tracking)
    return x + w_, y + h_


def chip_outline(d, xy, s, font, fg=WHITE, border=LINE, bg=None,
                 pad_x=32, pad_y=18, radius=16, tracking=0.0, width=2):
    x, y = xy
    w_ = tw(d, s, font, tracking) + pad_x * 2
    h_ = font.size + pad_y * 2
    d.rounded_rectangle([x, y, x + w_, y + h_], radius=radius, fill=bg,
                        outline=border, width=width)
    text(d, (x + pad_x, y + h_ / 2), s, font, fg, anchor="lm", tracking=tracking)
    return x + w_, y + h_


def panel(img: Image.Image, box, radius=28, fill=PANEL, outline=LINE_SOFT,
          width=2, glow_color=None):
    """Скруглённая панель на отдельном слое (мягко ложится поверх фона)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=radius, fill=fill + (255,),
                        outline=outline + (255,), width=width)
    img.alpha_composite(layer)
    return img


def divider(d, x1, y, x2, color=LINE, width=2):
    d.line([x1, y, x2, y], fill=color, width=width)


def dot(d, cx, cy, r, fill, outline=None, width=0):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)


def number_badge(img: Image.Image, cx, cy, n: str, r=46, fill=GOLD, fg=GRAPHITE,
                 font=None):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill + (255,))
    d.text((cx, cy + 2), n, font=font or F(800, int(r * 0.95)), fill=fg, anchor="mm")
    img.alpha_composite(layer)


# ---------------------------------------------------------------- каркас слайда
def header(img: Image.Image, idx: int, total: int = 7, tag: str = "ONELITE GOLD"):
    d = ImageDraw.Draw(img)
    f = F(800, 30)
    draw_tracked(d, (M, TOP_BAR_Y), tag, f, GOLD, 5.2)
    w_ = tw(d, tag, f, 5.2)
    d.line([M, TOP_BAR_Y + 50, M + w_, TOP_BAR_Y + 50], fill=GOLD_D, width=3)
    # номер слайда
    f2 = F(700, 30)
    s = f"{idx:02d} / {total:02d}"
    d.text((W - M, TOP_BAR_Y + 8), s, font=f2, fill=GRAY_D, anchor="ra")


def footer(img: Image.Image, idx: int, total: int = 7,
           left: str = "OneLite Gold · Зернистость P100 · Ø 125 мм · 8 отверстий",
           right: str | None = None):
    d = ImageDraw.Draw(img)
    divider(d, M, FOOT_Y, W - M, LINE_SOFT, 2)
    d.text((M, FOOT_Y + 34), left, font=F(500, 28), fill=GRAY_D)
    if right:
        d.text((W - M, FOOT_Y + 34), right, font=F(500, 28), fill=GRAY_D, anchor="ra")


def eyebrow(d, y, s, color=GOLD):
    draw_tracked(d, (M, y), s, F(800, 32), color, 3.6)
    return y + 62


def h1(d, y, s, size=104, color=WHITE, max_w=None, leading=1.06):
    f = F(800, size)
    lines = wrap(d, s, f, max_w or (W - 2 * M))
    lh = size * leading
    for i, line in enumerate(lines):
        d.text((M, y + i * lh), line, font=f, fill=color)
    return y + len(lines) * lh


def scene_note(d, xy, s="Иллюстрация. Не фотография товара."):
    d.text(xy, s, font=F(600, 28), fill=GRAY_D, anchor="la")


def paste_shadow(base: Image.Image, sprite: Image.Image, pos, blur=34, offset=(0, 22),
                 alpha=150):
    """Накладывает спрайт с мягкой тенью."""
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    a = sprite.getchannel("A").point(lambda v: min(255, int(v * alpha / 255)))
    black = Image.new("RGBA", sprite.size, (0, 0, 0, 255))
    black.putalpha(a)
    sh.alpha_composite(black, (pos[0] + offset[0], pos[1] + offset[1]))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh)
    base.alpha_composite(sprite, pos)


def gold_rule(d, x, y, w_, h=6, radius=3):
    d.rounded_rectangle([x, y, x + w_, y + h], radius=radius, fill=GOLD)


def bullet(d, x, y, s, font, fill=WHITE, gap=34, r=9, color=GOLD, max_w=None,
           leading=1.3):
    dot(d, x + r, y + font.size * 0.62, r, color)
    yy = para(d, (x + gap + r * 2 - 6, y), s, font, fill,
              max_w or (W - M - (x + gap + r * 2)), leading=leading)
    return yy


def dim_line(d, x1, y1, x2, y2, color=GOLD, width=3, cap=18, arrows=True):
    """Размерная линия со стрелками-засечками."""
    d.line([x1, y1, x2, y2], fill=color, width=width)
    if not arrows:
        return
    vx, vy = x2 - x1, y2 - y1
    L = max(1e-6, (vx * vx + vy * vy) ** 0.5)
    ux, uy = vx / L, vy / L
    px, py = -uy, ux
    for (bx, by, sx, sy) in ((x1, y1, ux, uy), (x2, y2, -ux, -uy)):
        d.line([bx, by, bx + sx * cap + px * cap * 0.55, by + sy * cap + py * cap * 0.55],
               fill=color, width=width)
        d.line([bx, by, bx + sx * cap - px * cap * 0.55, by + sy * cap - py * cap * 0.55],
               fill=color, width=width)
