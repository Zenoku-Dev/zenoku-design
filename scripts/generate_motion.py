#!/usr/bin/env python3
"""Генератор motion-версий README-баннеров zenoku (DESIGN 1.4).

Один приём на знак (logo-animation: draw-on для линейных знаков):
дуга → глиф → точка (zenoku) → wordmark. База = финальный кадр бренда,
CSS играет один раз и заканчивается на нём; без CSS и при
prefers-reduced-motion виден чистый знак 1.4.

Геометрия не хардкодится: длины штрихов вычисляются численно из тех же
строк, что рисует generate_svg.py, поэтому знаки всегда совпадают.

Запускать из корня репо: python3 scripts/generate_motion.py
Пост-валидация (XML + дубликаты атрибутов) встроена в main().
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_svg as G

EASE_DRAW = "cubic-bezier(.65,0,.35,1)"   # easeInOutCubic — ход штриха
EASE_OUT = "cubic-bezier(.22,1,.36,1)"    # easeOutQuint — появления


# ---------- числовая длина контуров ----------

def _cubic_len(p0, p1, p2, p3, n=96):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(n))


def _arc_length(d):
    m = re.match(r"M\s*([\-\d.]+)\s+([\-\d.]+)\s+A\s*([\-\d.]+)\s+([\-\d.]+)\s+0\s+(\d)\s+(\d)\s+([\-\d.]+)\s+([\-\d.]+)", d)
    if not m:
        return None
    x1, y1, rx, ry, large, _sweep, x2, y2 = (float(v) for v in m.groups())
    r = rx
    chord = math.dist((x1, y1), (x2, y2))
    theta = 2 * math.asin(min(chord / (2 * r), 1.0))
    if int(large):
        theta = 2 * math.pi - theta
    return r * theta


_TOKEN = re.compile(r"([MLVCHZ])|(-?\d+(?:\.\d+)?)")


def _path_length(d):
    arc = _arc_length(d)
    if arc is not None:
        return arc
    toks = [(a or b) for a, b in _TOKEN.findall(d)]
    i = 0
    cur = None
    start = None
    total = 0.0
    cmd = None

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        if re.fullmatch(r"[MLVCHZ]", toks[i]):
            cmd = toks[i]
            i += 1
            continue
        if cmd == "M":
            x, y = num(), num()
            cur = (x, y)
            start = cur
            cmd = "L"  # последующие пары в M — это L
        elif cmd == "L":
            x, y = num(), num()
            total += math.dist(cur, (x, y))
            cur = (x, y)
        elif cmd == "V":
            y = num()
            total += abs(y - cur[1])
            cur = (cur[0], y)
        elif cmd == "H":
            x = num()
            total += abs(x - cur[0])
            cur = (x, cur[1])
        elif cmd == "C":
            p1, p2, p3 = (num(), num()), (num(), num()), (num(), num())
            total += _cubic_len(cur, p1, p2, p3)
            cur = p3
        elif cmd == "Z":
            total += math.dist(cur, start)
            cur = start
        else:
            raise ValueError("unsupported path cmd %r in %r" % (cmd, d))
    return total


def _shape_length(tag):
    m = re.match(r"<(\w+)", tag)
    el = m.group(1)
    if el == "path":
        d = re.search(r'\sd="([^"]+)"', tag).group(1)
        return _path_length(d)
    if el == "rect":
        x = float(re.search(r'\sx="([\-\d.]+)"', tag).group(1))
        y = float(re.search(r'\sy="([\-\d.]+)"', tag).group(1))
        w = float(re.search(r'\swidth="([\-\d.]+)"', tag).group(1))
        h = float(re.search(r'\sheight="([\-\d.]+)"', tag).group(1))
        rxm = re.search(r'\srx="([\-\d.]+)"', tag)
        rx = float(rxm.group(1)) if rxm else 0.0
        return 2 * (w + h - 4 * rx) + 2 * math.pi * rx
    if el == "circle":
        r = float(re.search(r'\sr="([\-\d.]+)"', tag).group(1))
        return 2 * math.pi * r
    if el == "line":
        x1 = float(re.search(r'\sx1="([\-\d.]+)"', tag).group(1))
        y1 = float(re.search(r'\sy1="([\-\d.]+)"', tag).group(1))
        x2 = float(re.search(r'\sx2="([\-\d.]+)"', tag).group(1))
        y2 = float(re.search(r'\sy2="([\-\d.]+)"', tag).group(1))
        return math.dist((x1, y1), (x2, y2))
    if el == "polyline":
        pts = re.search(r'points="([^"]+)"', tag).group(1).split()
        pts = [tuple(float(n) for n in p.split(",")) for p in pts]
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    raise ValueError("unsupported shape %r" % el)


_SHAPE = re.compile(r"<(?:path|rect|polyline|line|circle)\b[^>]*>")


def _annotate(fragment, delay_start, delay_step):
    """Оборачивает каждый контур класса .draw2 с реальным --len и сдвигом."""
    out = []
    pos = 0
    idx = 0
    for m in _SHAPE.finditer(fragment):
        out.append(fragment[pos:m.start()])
        tag = m.group(0)
        length = _shape_length(tag)
        delay = delay_start + idx * delay_step
        style = f"--len:{length:.2f};animation-delay:{delay:.2f}s"
        tag = tag[:-2].rstrip() + f' class="draw2" style="{style}"/>'
        out.append(tag)
        pos = m.end()
        idx += 1
    out.append(fragment[pos:])
    return "".join(out)


# ---------- SVG: анимированные баннеры ----------

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


def animated_mark(product, color):
    if product == "zenoku":
        ring_len = 2 * math.pi * G.R
        return (f'<circle class="draw" style="--len:{ring_len:.2f}" '
                f'cx="{G.C}" cy="{G.C}" r="{G.R}" fill="none" stroke="{color}" stroke-width="{G.SW}"/>' + "\n" +
                f'<g class="dot"><circle cx="{G.C}" cy="{G.C}" r="4.0" fill="{color}"/></g>')
    arc = (f'<path class="draw" style="--len:{_path_length(G.ARC):.2f}" d="{G.ARC}" '
           f'fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>')
    glyph = _annotate(G.GLYPHS[product](color, color), 0.50, 0.07)
    inner = arc + "\n" + f'<g transform="translate({G.C} {G.C}) scale({G.GS}) translate(-{G.C} -{G.C})">\n{glyph}\n</g>'
    return inner


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
    wordmark = wordmark.replace("<path ", '<path class="word" ', 1)
    width = int(G.BANNER_TEXT_X + advance + G.BANNER_PAD)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {G.BANNER_H}" role="img" aria-label="{name} banner">
<title>{name}</title>
{style_block()}<rect x="{G.BANNER_PAD}" y="{G.BANNER_PAD}" width="{G.BANNER_TILE}" height="{G.BANNER_TILE}" rx="93" fill="{tile}"/>
<g transform="translate({tile_c} {tile_c}) scale({glyph_scale:.4f}) translate(-32 -32)">
{animated_mark(product, glyph)}
</g>
{wordmark}
</svg>
'''


def _validate(path, src):
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(src)
    except ET.ParseError as e:
        raise SystemExit(f"invalid SVG {path}: {e}")
    for m in re.finditer(r"<[^>]+>", src):
        attrs = re.findall(r"\s([a-zA-Z-]+)=", m.group(0))
        dup = {a for a in attrs if attrs.count(a) > 1}
        if dup:
            raise SystemExit(f"duplicate attribute(s) {dup} in {path}: {m.group(0)[:120]}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for product in G.NAMES:
        d = os.path.join(root, "assets", product)
        os.makedirs(d, exist_ok=True)
        for variant, fname in (("light", "readme-banner-animated.svg"),
                               ("dark", "readme-banner-animated-dark.svg")):
            path = os.path.join(d, fname)
            src = animated_banner_svg(product, variant)
            _validate(path, src)
            with open(path, "w") as f:
                f.write(src)
            print("wrote", path)


if __name__ == "__main__":
    main()
