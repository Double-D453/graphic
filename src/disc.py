"""Технический рендер шлифовального диска.

ВАЖНО: это условная схема, а не фотография товара. Геометрия (диаметр, число
отверстий) задаётся параметрами, чтобы случайно не изменить число отверстий.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ds import GOLD, GOLD_L, WHITE


def _lerp(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


def disc_render(diameter: int, holes: int = 8, seed: int = 7,
                hole_ring: float = 0.60, hole_d: float = 0.108,
                phase: float = 22.5) -> Image.Image:
    """Вид сверху. diameter — итоговый диаметр в px.

    hole_ring — радиус окружности центров отверстий (доля от радиуса диска),
    hole_d    — диаметр отверстия (доля от диаметра диска).
    """
    S = 2                                    # супер-сэмплинг
    D = int(diameter * S)
    pad = int(D * 0.11)
    n = D + pad * 2
    R = D / 2
    c = n / 2

    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    t = np.clip(r / R, 0, 1)

    # --- основа: радиальный градиент «графит»
    face = np.zeros((n, n, 3), np.float32)
    c_in, c_out = (86, 96, 100), (26, 32, 34)
    for i in range(3):
        face[..., i] = c_in[i] + (c_out[i] - c_in[i]) * (t ** 0.85)

    # --- зерно абразива: мелкий детерминированный шум + блёстки
    rng = np.random.default_rng(seed)
    grain = rng.normal(0, 7.5, (n, n, 1))
    speck = (rng.random((n, n, 1)) < 0.05) * rng.random((n, n, 1)) * 26
    face += grain + speck

    # --- мягкий тёплый блик (золотой свет) по диагонали
    sheen = np.clip(1.0 - (((xx - 0.70 * n) ** 2 / (0.52 * n) ** 2
                            + (yy - 0.30 * n) ** 2 / (0.60 * n) ** 2)), 0, 1) ** 1.6
    for i in range(3):
        face[..., i] += (GOLD_L[i] - 40) * sheen * 0.22

    # --- затемнение к краю (объём)
    edge_shade = np.clip((t - 0.80) / 0.20, 0, 1) ** 1.4 * 0.55
    face *= (1 - edge_shade)[..., None]

    alpha = np.clip((R - r) / (1.6 * S), 0, 1) * 255.0
    mask = Image.fromarray(alpha.astype(np.uint8), "L")
    img = Image.fromarray(np.clip(face, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    img.putalpha(mask)

    # Все детали рисуем на отдельном слое и накладываем — так не ломается прозрачность.
    det = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(det)

    # концентрические следы обработки абразивного слоя
    for frac, al in ((0.30, 26), (0.47, 22), (0.68, 18), (0.87, 30)):
        rr = R * frac
        d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(168, 178, 182, al),
                  width=max(1, S * 2))
    # дуги-риски от шлифовки
    rr0 = np.random.default_rng(seed + 5)
    for _ in range(18):
        rr = R * float(rr0.uniform(0.32, 0.95))
        a0 = float(rr0.uniform(0, 360))
        span = float(rr0.uniform(18, 70))
        d.arc([c - rr, c - rr, c + rr, c + rr], a0, a0 + span,
              fill=(206, 214, 218, int(rr0.uniform(16, 40))), width=max(1, S * 2))
    # --- отверстия
    hole_r = hole_d * D / 2
    ring = hole_ring * R
    for i in range(holes):
        ang = np.deg2rad(-90 + phase + i * (360.0 / holes))
        hx, hy = c + ring * np.cos(ang), c + ring * np.sin(ang)
        d.ellipse([hx - hole_r, hy - hole_r, hx + hole_r, hy + hole_r],
                  fill=(11, 15, 16, 255))
        # объём отверстия: светлая нижняя дуга + тёмная верхняя
        d.arc([hx - hole_r, hy - hole_r + 2, hx + hole_r, hy + hole_r + 2],
              200, 340, fill=(120, 132, 136, 130), width=max(2, S * 2))
        d.arc([hx - hole_r, hy - hole_r - 1, hx + hole_r, hy + hole_r - 1],
              15, 165, fill=(0, 0, 0, 150), width=max(2, S * 2))

    # --- кромка
    d.ellipse([c - R, c - R, c + R, c + R], outline=(6, 8, 9, 235),
              width=max(3, S * 5))
    d.ellipse([c - R + S * 4, c - R + S * 4, c + R - S * 4, c + R - S * 4],
              outline=(96, 106, 110, 90), width=max(2, S * 2)
              if False else max(2, S * 2))
    # нейтральная подсветка кромки (цвет товара не подменяем)
    d.arc([c - R + S * 11, c - R + S * 11, c + R - S * 11, c + R - S * 11],
          286, 352, fill=(214, 222, 226, 88), width=max(2, S * 4))
    d.arc([c - R + S * 11, c - R + S * 11, c + R - S * 11, c + R - S * 11],
          6, 74, fill=(74, 82, 86, 110), width=max(2, S * 4))

    # накладываем детали и возвращаем круглую маску
    img.alpha_composite(det)
    img.putalpha(mask)
    return img.resize((int(round(n / S)), int(round(n / S))), Image.LANCZOS)


def disc_scheme(size: int, holes: int = 8, hole_ring: float = 0.60,
                hole_d: float = 0.108, phase: float = 22.5,
                line=GOLD, dim=GOLD_L, fill=None) -> Image.Image:
    """Линейная схема диска (вид сверху) — для технических слайдов."""
    S = 2
    n = int(size * S)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    R = n / 2 - 4 * S
    c = n / 2
    if fill:
        d.ellipse([c - R, c - R, c + R, c + R], fill=fill)
    d.ellipse([c - R, c - R, c + R, c + R], outline=line + (255,), width=max(2, S * 4))
    d.ellipse([c - R * 0.94, c - R * 0.94, c + R * 0.94, c + R * 0.94],
              outline=line + (70,), width=max(1, S * 2))
    hole_r = hole_d * (2 * R) / 2
    ring = hole_ring * R
    for i in range(holes):
        ang = np.deg2rad(-90 + phase + i * (360.0 / holes))
        hx, hy = c + ring * np.cos(ang), c + ring * np.sin(ang)
        d.ellipse([hx - hole_r, hy - hole_r, hx + hole_r, hy + hole_r],
                  fill=(14, 19, 20, 255), outline=line + (255,), width=max(2, S * 3))
    return img.resize((size, size), Image.LANCZOS)


def disc_perspective(diameter: int, holes: int = 8, tilt: float = 0.46,
                     seed: int = 7, phase: float = 22.5) -> Image.Image:
    """Диск в лёгкой перспективе (сжат по вертикали) — для крупных планов."""
    src = disc_render(diameter, holes=holes, seed=seed, phase=phase)
    h = int(src.size[1] * tilt)
    return src.resize((src.size[0], h), Image.LANCZOS)


def grain_swatch(size: int, density: float = 0.30, grain_px: float = 2.4,
                 seed: int = 5, base=(74, 82, 86), spark=(196, 206, 210)) -> Image.Image:
    """Условная текстура абразивного слоя: мелкое зерно + следы шлифовки.

    Схема, а не фотография товара.
    """
    S = 2
    n = int(size * S)
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    t = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2)
    arr = np.zeros((n, n, 3), np.float32)
    for i in range(3):
        arr[..., i] = base[i] * (1 - 0.62 * np.clip(t, 0, 1) ** 1.25)

    # зерно: мелкая равномерная крошка
    k = max(2, int(grain_px * S))
    g = n // k + 1
    dots = (rng.random((g, g)) < density).astype(np.float32)
    dots *= rng.random((g, g)).astype(np.float32)
    gran = np.kron(dots, np.ones((k, k)))[:n, :n]
    gran = gran * 0.55 + rng.random((n, n)).astype(np.float32) * 0.16
    arr += (gran * 1.35)[..., None] * np.array(spark, np.float32) / 255.0 * 255.0 * 0.42
    arr += rng.normal(0, 3.2, (n, n, 1))

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # следы шлифовки — концентрические дуги
    d = ImageDraw.Draw(img)
    c = n / 2
    for _ in range(30):
        rr = float(rng.uniform(0.10, 0.98)) * (n / 2)
        a0 = float(rng.uniform(0, 360))
        span = float(rng.uniform(15, 80))
        d.arc([c - rr, c - rr, c + rr, c + rr], a0, a0 + span,
              fill=(226, 232, 234, int(rng.uniform(20, 52))), width=max(1, S))
    d.ellipse([0, 0, n - 1, n - 1], outline=(255, 255, 255, 40), width=max(2, S * 2))

    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, n - 1, n - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(S * 1.2))
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)
