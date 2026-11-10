#!/usr/bin/env python3
"""Генератор motion-версий README-баннеров zenoku.

Один приём на знак (лого-скилл: draw-on для линейных знаков):
дуга → глиф → точка (zenoku) → wordmark. База = финальный кадр бренда,
CSS-анимации играют один раз и заканчиваются на нём; при отсутствии
поддержки CSS/SMIL и при prefers-reduced-motion виден чистый знак.

Запускать из корня репо: python3 scripts/generate_motion.py
PNG/MP4-рендер — scripts/render_sting.py + scripts/render.sh.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_svg as G

EASE_DRAW = "cubic-bezier(.65,0,.35,1)"   # easeInOutCubic — ход штриха
EASE_OUT = "cubic-bezier(.22,1,.36,1)"    # easeOutQuint — появления


LENGTHS = {"arc": 115.19, "ring": 138.23, "shield": 85.45,
           "zent_rect": 91.16, "zent_poly": 31.85,
           "auth_circle": 38.96, "auth_line": 11.2,
           "rsh_poly": 21.64, "rsh_line": 9.8}


def style_block():
    return f"""<style>
.draw{{stroke-dasharray:var(--len);stroke-dashoffset:0;animation:draw 1s .15s {EASE_DRAW} backwards}}
.draw2{{stroke-dasharray:var(--len);stroke-dashoffset:0;animation:draw 1s .45s {EASE_DRAW} backwards}}
@keyframes draw{{from{{stroke-dashoffset:var(--len)}}to{{stroke-dashoffset:0}}}}
.word{{animation:rise .7s .72s {EASE_OUT} backwards}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.dot{{transform-box:fill-box;transform-origin:center;animation:pop .5s .95s cubic-bezier(.22,1.36,.36,1) backwards}}
@keyframes pop{{from{{transform:scale(0)}}to{{transform:scale(1)}}}}
@media (prefers-reduced-motion: reduce){{.draw,.draw2,.word,.dot{{animation:none}}}}
</style>
"""


def animated_body(product, color):
    """Знак с CSS-классами движения. База = финальный кадр."""
    arc = (
        f'<path class="draw" style="--len:115.19" d="{G.ARC}" fill="none" '
        f'stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>'
    )
    if product == "zenoku":
        return (
            f'<circle class="draw" style="--len:138.23" cx="{G.C}" cy="{G.C}" r="{G.R}" '
            f'fill="none" stroke="{color}" stroke-width="{G.SW}"/>\n'
            f'<g class="dot"><circle cx="{G.C}" cy="{G.C}" r="4.4" fill="{color}"/></g>'
        )
    glyphs = {
        "zeno": f'<path class="draw2" style="--len:85.45" d="M 32 17 L 43.2 21.1 V 30.2 C 43.2 38.7 39.3 44 32 47.1 C 24.7 44 20.8 38.7 20.8 30.2 V 21.1 Z" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linejoin="round"/>',
        "zent": (
            f'<rect class="draw2" style="--len:91.16" x="16.5" y="23.5" width="31" height="17.5" rx="3.4" fill="none" stroke="{color}" stroke-width="{G.SW}"/>\n'
            f'<polyline class="draw2" style="--len:31.85" points="19,26.6 32,35.8 45,26.6" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" stroke-linejoin="round" style="animation-delay:.55s"/>'
        ),
        "auth": (
            f'<circle class="draw2" style="--len:38.96" cx="32" cy="25.2" r="6.2" fill="none" stroke="{color}" stroke-width="{G.SW}"/>\n'
            f'<line class="draw2" style="--len:11.2" x1="32" y1="30.4" x2="32" y2="41.6" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" style="animation-delay:.58s"/>'
        ),
        "rsh": (
            f'<polyline class="draw2" style="--len:21.64" points="20.8,24.2 28.6,31.7 20.8,39.2" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" stroke-linejoin="round"/>\n'
            f'<line class="draw2" style="--len:9.8" x1="33.2" y1="39.2" x2="43.0" y2="39.2" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" style="animation-delay:.58s"/>'
        ),
    }
    return arc + "\n" + glyphs[product]


def animated_banner_svg(product, variant):
    if variant == "light":
        tile, glyph, text = G.INK, G.PAPER, G.INK
    else:
        tile, glyph, text = G.PAPER, G.INK, G.PAPER
    name = G.NAMES[product]
    tile_c = G.BANNER_PAD + G.BANNER_TILE / 2
    glyph_scale = G.BANNER_TILE / 64 * 0.775
    baseline = round(G.BANNER_H / 2 + G.BANNER_EM * G.x_height_ratio() / 2, 1)
    wordmark, advance = G.text_to_path(name, G.BANNER_TEXT_X, baseline, G.BANNER_EM, text)
    # оборачиваем wordmark-path классом .word (первый элемент пути — class)
    wordmark = wordmark.replace("<path ", '<path class="word" ', 1)
    width = int(G.BANNER_TEXT_X + advance + G.BANNER_PAD)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {G.BANNER_H}" role="img" aria-label="{name} banner">
<title>{name}</title>
{style_block()}<rect x="{G.BANNER_PAD}" y="{G.BANNER_PAD}" width="{G.BANNER_TILE}" height="{G.BANNER_TILE}" rx="93" fill="{tile}"/>
<g transform="translate({tile_c} {tile_c}) scale({glyph_scale:.4f}) translate(-32 -32)">
{animated_body(product, glyph)}
</g>
{wordmark}
</svg>
'''


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for product in G.NAMES:
        d = os.path.join(root, "assets", product)
        os.makedirs(d, exist_ok=True)
        for variant, fname in (("light", "readme-banner-animated.svg"),
                               ("dark", "readme-banner-animated-dark.svg")):
            path = os.path.join(d, fname)
            with open(path, "w") as f:
                f.write(animated_banner_svg(product, variant))
            print("wrote", path)


if __name__ == "__main__":
    main()
