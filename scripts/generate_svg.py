#!/usr/bin/env python3
"""Генератор SVG-ассетов zenoku-design.

Единственный источник правды по геометрии знаков. Запускать из корня репо:
    python3 scripts/generate_svg.py
PNG-экспорт — scripts/render.sh (нужен rsvg-convert).
"""
import math
import os

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

BRIGENDS_PATH = os.path.expanduser("~/intemp/font.otf")  # Brigends Expanded Regular (Multype Studio)

C = 32  # центр сетки 64×64
R = 19  # радиус общей дуги / кольца
SW = 3.2  # толщина штриха
GS = 0.76  # масштаб глифа относительно сетки (inset, защита от наслоения на дугу)

INK = "#000000"     # чистый чёрный
PAPER = "#FFFFFF"   # чистый белый

# Дуга 300°: разрыв 60°, центр разрыва на СВ (−45°).
# В экранных координатах угол растёт по часовой; дуга идёт от −15° до 285°.
def polar(cx, cy, r, deg):
    rad = math.radians(deg)
    return (cx + r * math.cos(rad), cy + r * math.sin(rad))

P1 = polar(C, C, R, -15)
P2 = polar(C, C, R, 285)
ARC = f"M {P1[0]:.2f} {P1[1]:.2f} A {R} {R} 0 1 1 {P2[0]:.2f} {P2[1]:.2f}"


def arc(color):
    return (
        f'<path d="{ARC}" fill="none" stroke="{color}" stroke-width="{SW}" '
        f'stroke-linecap="round"/>'
    )


def full_ring(color):
    return f'<circle cx="{C}" cy="{C}" r="{R}" fill="none" stroke="{color}" stroke-width="{SW}"/>'


def dot(color):
    return f'<circle cx="{C}" cy="{C}" r="4.0" fill="{color}"/>'


def _inner(product, fg):
    # дуга общая (не масштабируется), глиф сжат к центру — без наслоения
    body = arc(fg) + "\n" + f'<g transform="translate(32 32) scale({GS}) translate(-32 -32)">\n{GLYPHS[product](fg, fg)}\n</g>'
    return body


GLYPHS = {
    # zeno — щит (проверка файла, вердикт движков)
    "zeno": lambda ink, accent: f'''<path d="M 32 17 L 43.2 21.1 V 30.2 C 43.2 38.7 39.3 44 32 47.1 C 24.7 44 20.8 38.7 20.8 30.2 V 21.1 Z" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linejoin="round"/>''',
    # zent — конверт (почта): корпус + клапан-«галка»
    "zent": lambda ink, accent: f'''<rect x="16.5" y="23.5" width="31" height="17.5" rx="3.4" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<polyline points="19,26.6 32,35.8 45,26.6" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>''',
    # auth — замочная скважина (единая авторизация): круг + расходящиеся линии (слои)
    "auth": lambda ink, accent: f'''<circle cx="32" cy="24.9" r="5.7" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<line x1="29.5" y1="28.15" x2="27.25" y2="40.9" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>
<line x1="34.5" y1="28.15" x2="36.75" y2="40.9" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # rsh — приглашение терминала (>_)
    "rsh": lambda ink, accent: f'''<polyline points="20.8,24.2 28.6,31.7 20.8,39.2" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="33.2" y1="39.2" x2="43.0" y2="39.2" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # zenoku — кольцо + точка (целое и точка отсчёта)
    "zenoku": lambda ink, accent: full_ring(ink) + "\n" + dot(accent),
    # zenoku-dev — организация: дуга + </> (код zenoku), слэш в стороне от скобок
    "zenoku-dev": lambda ink, accent: f'''<polyline points="25.2,22.8 18.4,31.75 25.2,40.7" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="38.8,22.8 45.6,31.75 38.8,40.7" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="34.6" y1="22.5" x2="29.4" y2="41.0" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
}

NAMES = {"zenoku": "zenoku", "zeno": "zeno", "zent": "zent", "rsh": "rsh", "auth": "auth", "zenoku-dev": "zenoku-dev"}

_FONT = None


def _font():
    global _FONT
    if _FONT is None:
        _FONT = TTFont(BRIGENDS_PATH)
    return _FONT


def text_to_path(text, x, baseline, em, fill):
    f = _font()
    upem = f["head"].unitsPerEm
    scale = em / upem
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    glyph_set = f.getGlyphSet()
    parts = []
    cx = x
    track = em * 0.03  # трекинг wordmark
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            cx += (upem // 3) * scale + track
            continue
        pen = SVGPathPen(glyph_set)
        tpen = TransformPen(pen, (scale, 0, 0, -scale, cx, baseline))
        glyph_set[name].draw(tpen)
        d = pen.getCommands()
        if d:
            parts.append(d)
        cx += hmtx[name][0] * scale + track
    # стилизация: мягкое расширение штрихом в цвет заливки — углы получают
    # собственное скругление (правка исходных кривых, а не «шрифт как есть»)
    sw = round(em * 0.022, 2)
    return (f'<path d="{" ".join(parts)}" fill="{fill}" stroke="{fill}" '
            f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>',
            cx - x - track)


def x_height_ratio():
    f = _font()
    os2 = f.get("OS/2")
    if os2 is not None and getattr(os2, "sxHeight", 0):
        return os2.sxHeight / f["head"].unitsPerEm
    return 0.5

# README-баннер: иконка слева, название крупно справа в одну строку.
BANNER_H = 512
BANNER_PAD = 48
BANNER_TILE = 416
BANNER_TEXT_X = BANNER_PAD + BANNER_TILE + 72
BANNER_EM = 240
BANNER_GAP = round(BANNER_EM * 0.6, 2)


def mark_svg(product, fg):
    glyph = GLYPHS[product](fg, fg)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAMES[product]} mark">
<title>{NAMES[product]}</title>
{full_ring(fg) + chr(10) + dot(fg) if product == "zenoku" else _inner(product, fg)}
</svg>
'''


def logo_svg(product, fg, text_color):
    name = NAMES[product]
    em = 29
    text_x = 80
    baseline = round(32 + em * x_height_ratio() / 2, 1)
    wordmark, advance = text_to_path(name, text_x, baseline, em, text_color)
    width = int(text_x + advance + 16)
    if product == "zenoku":
        body = full_ring(fg) + "\n" + dot(fg)
    else:
        body = _inner(product, fg)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" role="img" aria-label="{name} logo">
<title>{name}</title>
{body}
{wordmark}
</svg>
'''


def app_icon_svg(product, tile, glyph_color):
    body = _icon_body(product, glyph_color)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" role="img" aria-label="{NAMES[product]} app icon">
<title>{NAMES[product]} app icon</title>
<rect width="1024" height="1024" rx="229" fill="{tile}"/>
<g transform="translate(512 512) scale(10.8) translate(-32 -32)">
{body}
</g>
</svg>
'''


def favicon_svg(product):
    if product == "zenoku":
        body = full_ring(PAPER) + "\n" + dot(PAPER)
    else:
        body = _inner(product, PAPER)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAMES[product]} favicon">
<title>{NAMES[product]}</title>
<rect width="64" height="64" rx="14.3" fill="{INK}"/>
{body}
</svg>
'''


def _icon_body(product, glyph_color):
    if product == "zenoku":
        return full_ring(glyph_color) + "\n" + dot(glyph_color)
    return _inner(product, glyph_color)


def banner_svg(product, variant):
    # variant: light — чёрный тайл + чёрный текст (на белом GitHub),
    #          dark  — белый тайл + белый текст (на тёмном GitHub)
    if variant == "light":
        tile, glyph, text = INK, PAPER, INK
    else:
        tile, glyph, text = PAPER, INK, PAPER
    name = NAMES[product]
    tile_c = BANNER_PAD + BANNER_TILE / 2
    glyph_scale = BANNER_TILE / 64 * 0.70
    baseline = round(BANNER_H / 2 + BANNER_EM * x_height_ratio() / 2, 1)
    wordmark, advance = text_to_path(name, BANNER_TEXT_X, baseline, BANNER_EM, text)
    width = int(BANNER_TEXT_X + advance + BANNER_PAD)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {BANNER_H}" role="img" aria-label="{name} banner">
<title>{name}</title>
<rect x="{BANNER_PAD}" y="{BANNER_PAD}" width="{BANNER_TILE}" height="{BANNER_TILE}" rx="93" fill="{tile}"/>
<g transform="translate({tile_c} {tile_c}) scale({glyph_scale:.4f}) translate(-32 -32)">
{_icon_body(product, glyph)}
</g>
{wordmark}
</svg>
'''


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for product in NAMES:
        d = os.path.join(root, "assets", product)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "mark.svg"), "w") as f:
            f.write(mark_svg(product, INK))
        with open(os.path.join(d, "mark-on-dark.svg"), "w") as f:
            f.write(mark_svg(product, PAPER))
        with open(os.path.join(d, "logo.svg"), "w") as f:
            f.write(logo_svg(product, INK, INK))
        with open(os.path.join(d, "logo-dark.svg"), "w") as f:
            f.write(logo_svg(product, PAPER, PAPER))
        with open(os.path.join(d, "app-icon.svg"), "w") as f:
            f.write(app_icon_svg(product, INK, PAPER))
        with open(os.path.join(d, "app-icon-paper.svg"), "w") as f:
            f.write(app_icon_svg(product, PAPER, INK))
        with open(os.path.join(d, "favicon.svg"), "w") as f:
            f.write(favicon_svg(product))
        with open(os.path.join(d, "readme-banner.svg"), "w") as f:
            f.write(banner_svg(product, "light"))
        with open(os.path.join(d, "readme-banner-dark.svg"), "w") as f:
            f.write(banner_svg(product, "dark"))
    print("svg ok")


if __name__ == "__main__":
    main()
