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
SW = 5  # толщина штриха

INK = "#221F1C"     # суми (тёплая почти-чёрная)
PAPER = "#FAF7F2"   # васи (тёплая бумага)
ACCENT = "#C2452D"  # циннабарь тории

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
    # zeno — линза (сканер файла, отчёт о хэшах)
    "zeno": lambda ink, accent: f'''<circle cx="29" cy="28.2" r="6.6" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<line x1="33.7" y1="32.9" x2="42.4" y2="41.6" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # zent — конверт (почта)
    "zent": lambda ink, accent: f'''<rect x="16.8" y="23.3" width="30.4" height="17.6" rx="3.1" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<polyline points="19.6,26.4 32,34.7 44.4,26.4" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>''',
    # auth — замочная скважина (единая авторизация)
    "auth": lambda ink, accent: f'''<circle cx="32" cy="26.4" r="5.1" fill="none" stroke="{ink}" stroke-width="{SW}"/>
<line x1="32" y1="29.6" x2="32" y2="41.4" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # rsh — приглашение терминала (>_)
    "rsh": lambda ink, accent: f'''<polyline points="20.8,24.2 28.6,31.7 20.8,39.2" fill="none" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="33.2" y1="39.2" x2="43.0" y2="39.2" stroke="{ink}" stroke-width="{SW}" stroke-linecap="round"/>''',
    # zenoku — кольцо + точка (целое и точка отсчёта). Единственный знак с циннабарью.
    "zenoku": lambda ink, accent: full_ring(ink) + "\n" + dot(accent),
}

NAMES = {"zenoku": "zenoku", "zeno": "zeno", "zent": "zent", "rsh": "rsh", "auth": "auth"}


def mark_svg(product, fg, dot_color=None):
    dot_color = dot_color or ACCENT
    glyph = GLYPHS[product](fg, dot_color)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAMES[product]} mark">
<title>{NAMES[product]}</title>
{glyph if product == "zenoku" else arc(fg) + chr(10) + glyph}
</svg>
'''


def logo_svg(product, fg, text_color, dot_color=ACCENT):
    name = NAMES[product]
    font_size = 29
    advance = round(font_size * 0.6, 2)  # JetBrains Mono advance = 0.6em
    text_x = 80
    width = int(text_x + advance * len(name) + 14)
    if product == "zenoku":
        body = full_ring(fg) + "\n" + dot(dot_color)
    else:
        body = arc(fg) + "\n" + GLYPHS[product](fg, dot_color)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" role="img" aria-label="{name} logo">
<title>{name}</title>
{body}
<text x="{text_x}" y="40.2" font-family="'JetBrains Mono','IBM Plex Mono',Menlo,Consolas,monospace" font-size="{font_size}" font-weight="600" fill="{text_color}">{name}</text>
</svg>
'''


def app_icon_svg(product, tile, glyph_color, dot_color=ACCENT):
    if product == "zenoku":
        body = full_ring(glyph_color) + "\n" + dot(dot_color)
    else:
        body = arc(glyph_color) + "\n" + GLYPHS[product](glyph_color, dot_color)
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
        body = full_ring(PAPER) + "\n" + dot(ACCENT)
    else:
        body = arc(PAPER) + "\n" + GLYPHS[product](PAPER, ACCENT)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAMES[product]} favicon">
<title>{NAMES[product]}</title>
<rect width="64" height="64" rx="14.3" fill="{INK}"/>
{body}
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
    print("svg ok")


if __name__ == "__main__":
    main()
