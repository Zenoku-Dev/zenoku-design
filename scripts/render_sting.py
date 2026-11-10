#!/usr/bin/env python3
"""Рендер MP4-стингов zenoku из параметрических SVG-кадров.

Кадр N рисует знак на доле хода t (дуга → глиф → точка → wordmark),
растрит rsvg-convert, собирает ffmpeg. Финал совпадает со статичным
знаком из generate_svg.py.

Запускать из корня репо: python3 scripts/render_sting.py [product ...]
Без аргументов — все пять + family.
"""
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_svg as G

FPS = 30
INK = G.INK
PAPER = G.PAPER
SIZE = 1080


def ease_in_out_cubic(p):
    return 4 * p**3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out_quint(p):
    return 1 - (1 - p) ** 5


def ease_out_back(p):
    c1 = 1.36
    return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2


def seg(t, start, dur):
    if t <= start:
        return 0.0
    if t >= start + dur:
        return 1.0
    return (t - start) / dur


def mark_group(product, cx, cy, scale, t, color):
    """Знак со штрихом, дорисованным на t∈[0,1]. Группа центрирована в (cx,cy)."""
    # реальные длины контуров (юзер-юниты, для rsvg/resvg): см. LENGTHS в generate_motion.py
    LEN = {"arc": 115.19, "ring": 138.23, "shield": 85.45,
           "zent_rect": 91.16, "zent_poly": 31.85,
           "auth_circle": 38.96, "auth_line": 11.2,
           "rsh_poly": 21.64, "rsh_line": 9.8}

    def dash(length, delay, dur):
        q = ease_in_out_cubic(seg(t, delay, dur))
        return f'stroke-dasharray="{length:.2f}" stroke-dashoffset="{length * (1 - q):.3f}"'

    inner = []
    if product == "zenoku":
        inner.append(f'<circle {dash(LEN["ring"], 0.0, 1.0)} cx="{G.C}" cy="{G.C}" r="{G.R}" fill="none" stroke="{color}" stroke-width="{G.SW}"/>')
        dp = ease_out_back(seg(t, 0.85, 0.45))
        dp = max(dp, 0.0)
        inner.append(f'<g transform="translate({G.C} {G.C}) scale({dp:.4f}) translate(-{G.C} -{G.C})"><circle cx="{G.C}" cy="{G.C}" r="4.4" fill="{color}"/></g>')
    else:
        inner.append(f'<path {dash(LEN["arc"], 0.0, 1.0)} d="{G.ARC}" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>')
        g = {
            "zeno": f'<path {dash(LEN["shield"], 0.35, 0.85)} d="M 32 17 L 43.2 21.1 V 30.2 C 43.2 38.7 39.3 44 32 47.1 C 24.7 44 20.8 38.7 20.8 30.2 V 21.1 Z" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linejoin="round"/>',
            "zent": (f'<rect {dash(LEN["zent_rect"], 0.35, 0.85)} x="16.5" y="23.5" width="31" height="17.5" rx="3.4" fill="none" stroke="{color}" stroke-width="{G.SW}"/>'
                     f'<polyline {dash(LEN["zent_poly"], 0.55, 0.7)} points="19,26.6 32,35.8 45,26.6" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" stroke-linejoin="round"/>'),
            "auth": (f'<circle {dash(LEN["auth_circle"], 0.35, 0.85)} cx="32" cy="25.2" r="6.2" fill="none" stroke="{color}" stroke-width="{G.SW}"/>'
                     f'<line {dash(LEN["auth_line"], 0.58, 0.65)} x1="32" y1="30.4" x2="32" y2="41.6" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>'),
            "rsh": (f'<polyline {dash(LEN["rsh_poly"], 0.35, 0.85)} points="20.8,24.2 28.6,31.7 20.8,39.2" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round" stroke-linejoin="round"/>'
                    f'<line {dash(LEN["rsh_line"], 0.58, 0.65)} x1="33.2" y1="39.2" x2="43.0" y2="39.2" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>'),
        }[product]
        inner.append(g)
    body = "\n".join(inner)
    return f'<g transform="translate({cx} {cy}) scale({scale}) translate(-32 -32)">\n{body}\n</g>'


def wordmark_group(product, cx, baseline, em, t, color):
    name = G.NAMES[product]
    p = ease_out_quint(seg(t, 0.72, 0.75))
    op = p
    dy = 16 * (1 - p)
    mark, advance = G.text_to_path(name, 0, 0, em, color)
    return (f'<g opacity="{op:.4f}" transform="translate({cx - advance / 2:.2f} {baseline + dy:.2f})">\n'
            f'{mark}\n</g>')


def frame_product(product, t):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">
<rect width="{SIZE}" height="{SIZE}" fill="{INK}"/>
{mark_group(product, SIZE / 2, 430, 6.4, t, PAPER)}
{wordmark_group(product, SIZE / 2, 880, 92, t, PAPER)}
</svg>'''


def frame_family(t):
    parts = [f'<rect width="{SIZE}" height="{SIZE}" fill="{INK}"/>']
    if t < 2.9:
        # Фаза 1: zenoku в центре
        local = min(t / 2.5, 1.0)
        parts.append(mark_group("zenoku", SIZE / 2, 430, 6.4, local, PAPER))
        parts.append(wordmark_group("zenoku", SIZE / 2, 880, 92, local, PAPER))
    elif t < 7.0:
        # Фаза 2: сетка 2×2 продуктов
        local = t - 2.9
        fade = ease_out_quint(seg(local, 0.0, 0.4))
        cells = [("zeno", 270, 330), ("zent", 810, 330), ("rsh", 270, 760), ("auth", 810, 760)]
        parts.append(f'<g opacity="{fade:.4f}">')
        for i, (prod, cx, cy) in enumerate(cells):
            lt = local - i * 0.4
            if lt <= 0:
                continue
            lt = min(lt / 2.2, 1.0)
            parts.append(mark_group(prod, cx, cy - 40, 3.1, lt, PAPER))
            parts.append(wordmark_group(prod, cx, cy + 165, 46, lt, PAPER))
        parts.append('</g>')
    else:
        # Фаза 3: возврат к zenoku
        local = min((t - 7.0) / 1.4, 1.0)
        parts.append(mark_group("zenoku", SIZE / 2, 430, 6.4, local, PAPER))
        parts.append(wordmark_group("zenoku", SIZE / 2, 880, 92, local, PAPER))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">\n' + "\n".join(parts) + "\n</svg>"


def render(frames, out_path, frame_svg):
    with tempfile.TemporaryDirectory(prefix="sting-", dir=os.path.dirname(out_path) or ".") as td:
        for i in range(frames):
            t = i / FPS
            svg = frame_svg(t)
            svg_path = os.path.join(td, f"f{i:04d}.svg")
            png_path = os.path.join(td, f"f{i:04d}.png")
            with open(svg_path, "w") as f:
                f.write(svg)
            subprocess.run(["rsvg-convert", "-w", str(SIZE), "-o", png_path, svg_path], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(td, "f%04d.png"),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart",
             out_path],
            check=True, capture_output=True)
    print("wrote", out_path)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "assets", "motion")
    os.makedirs(out_dir, exist_ok=True)
    targets = sys.argv[1:] or ["zenoku", "zeno", "zent", "rsh", "auth", "family"]
    for target in targets:
        if target == "family":
            render(int(10.6 * FPS), os.path.join(out_dir, "sting-family.mp4"), frame_family)
        else:
            render(int(4.2 * FPS), os.path.join(out_dir, f"sting-{target}.mp4"),
                   lambda t, p=target: frame_product(p, min(t / 2.6, 1.0)))


if __name__ == "__main__":
    main()
