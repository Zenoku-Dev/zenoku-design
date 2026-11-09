#!/usr/bin/env python3
"""Генератор SVG-ассетов zenoku-design.

Единственный источник правды по геометрии знаков. Запускать из корня репо:
    python3 scripts/generate_svg.py
PNG-экспорт — scripts/render.sh (нужен rsvg-convert).
"""
import math
import os

C = 32  # центр сетки 64×64
R = 22  # радиус общей дуги / кольца
SW = 4  # толщина штриха

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
    return f'<circle cx="{C}" cy="{C}" r="4.4" fill="{color}"/>'


GLYPHS = {
    # zeno — щит (проверка файла, вердикт движков)
    "zeno": lambda ink, accent: f'''<path d="M 32 17 L 43.2 21.1 V 30.2 C 43.2 38.7 39.3 44 32 47.1 C 24.7 44 20.8 38.7 20.8 30.2 V 21.1 Z" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linejoin="round"/>''',
    # zent — конверт (почта): корпус + клапан-«галка»
    "zent": lambda ink, accent: f'''<rect x="16.5" y="23.5" width="31" height="17.5" rx="3.4" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<polyline points="19,26.6 32,35.8 45,26.6" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>''',
    # auth — замочная скважина (единая авторизация): круг + стержень
    "auth": lambda ink, accent: f'''<circle cx="32" cy="25.2" r="6.2" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<line x1="32" y1="30.4" x2="32" y2="41.6" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # rsh — приглашение терминала (>_)
    "rsh": lambda ink, accent: f'''<polyline points="20.8,24.2 28.6,31.7 20.8,39.2" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="33.2" y1="39.2" x2="43.0" y2="39.2" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # zenoku — кольцо + точка (целое и точка отсчёта)
    "zenoku": lambda ink, accent: full_ring(ink) + "\n" + dot(accent),
}

NAMES = {"zenoku": "zenoku", "zeno": "zeno", "zent": "zent", "rsh": "rsh", "auth": "auth"}

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
{glyph if product == "zenoku" else arc(fg) + chr(10) + glyph}
</svg>
'''


def logo_svg(product, fg, text_color):
    name = NAMES[product]
    font_size = 29
    advance = round(font_size * 0.6, 2)  # JetBrains Mono advance = 0.6em
    text_x = 80
    width = int(text_x + advance * len(name) + 14)
    if product == "zenoku":
        body = full_ring(fg) + "\n" + dot(fg)
    else:
        body = arc(fg) + "\n" + GLYPHS[product](fg, fg)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" role="img" aria-label="{name} logo">
<title>{name}</title>
{body}
<text x="{text_x}" y="40.2" font-family="'JetBrains Mono','IBM Plex Mono',Menlo,Consolas,monospace" font-size="{font_size}" font-weight="600" fill="{text_color}">{name}</text>
</svg>
'''


def app_icon_svg(product, tile, glyph_color):
    body = _icon_body(product, glyph_color)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" role="img" aria-label="{NAMES[product]} app icon">
<title>{NAMES[product]} app icon</title>
<rect width="1024" height="1024" rx="229" fill="{tile}"/>
<g transform="translate(512 512) scale(12.4) translate(-32 -32)">
{body}
</g>
</svg>
'''


def favicon_svg(product):
    if product == "zenoku":
        body = full_ring(PAPER) + "\n" + dot(PAPER)
    else:
        body = arc(PAPER) + "\n" + GLYPHS[product](PAPER, PAPER)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAMES[product]} favicon">
<title>{NAMES[product]}</title>
<rect width="64" height="64" rx="14.3" fill="{INK}"/>
{body}
</svg>
'''


def _icon_body(product, glyph_color):
    if product == "zenoku":
        return full_ring(glyph_color) + "\n" + dot(glyph_color)
    return arc(glyph_color) + "\n" + GLYPHS[product](glyph_color, glyph_color)


def banner_svg(product, variant):
    # variant: light — чёрный тайл + чёрный текст (на белом GitHub),
    #          dark  — белый тайл + белый текст (на тёмном GitHub)
    if variant == "light":
        tile, glyph, text = INK, PAPER, INK
    else:
        tile, glyph, text = PAPER, INK, PAPER
    name = NAMES[product]
    width = int(BANNER_TEXT_X + BANNER_GAP * len(name) + BANNER_PAD)
    tile_c = BANNER_PAD + BANNER_TILE / 2
    glyph_scale = BANNER_TILE / 64 * 0.775
    baseline = BANNER_H / 2 + BANNER_EM * 0.36
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {BANNER_H}" role="img" aria-label="{name} banner">
<title>{name}</title>
<rect x="{BANNER_PAD}" y="{BANNER_PAD}" width="{BANNER_TILE}" height="{BANNER_TILE}" rx="93" fill="{tile}"/>
<g transform="translate({tile_c} {tile_c}) scale({glyph_scale:.4f}) translate(-32 -32)">
{_icon_body(product, glyph)}
</g>
<text x="{BANNER_TEXT_X}" y="{baseline:.1f}" font-family="'JetBrains Mono','IBM Plex Mono',Menlo,Consolas,monospace" font-size="{BANNER_EM}" font-weight="600" fill="{text}">{name}</text>
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
