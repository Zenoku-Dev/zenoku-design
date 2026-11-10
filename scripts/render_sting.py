#!/usr/bin/env python3
"""Рендер MP4-стингов zenoku из параметрических SVG-кадров (DESIGN 1.4).

Кадр t рисует знак на доле хода t (дуга → глиф → точка → wordmark),
растрит rsvg-convert, собирает ffmpeg. Длины берутся из generate_motion,
геометрия — из generate_svg.py: финал совпадает со статичным знаком.

Запускать из корня репо: python3 scripts/render_sting.py [product ...]
Без аргументов — все шесть + family.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_svg as G
import generate_motion as M

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


def dash_attrs(length, q):
    return f'stroke-dasharray="{length:.2f}" stroke-dashoffset="{length * (1 - q):.3f}"'


def _annotated(fragment, t, delay0, step, dur, color):
    """Каждому контуру — штрих, дорисованный на q_i(t)."""
    out = []
    pos = 0
    idx = 0
    for m in M._SHAPE.finditer(fragment):
        out.append(fragment[pos:m.start()])
        tag = m.group(0)
        length = M._shape_length(tag)
        q = ease_in_out_cubic(seg(t, delay0 + idx * step, dur))
        if tag.endswith("/>"):
            tag = tag[:-2].rstrip() + f' {dash_attrs(length, q)}/>'
        else:
            tag = tag[:-1].rstrip() + f' {dash_attrs(length, q)}>'
        out.append(tag)
        pos = m.end()
        idx += 1
    out.append(fragment[pos:])
    return "".join(out)


def mark_group(product, cx, cy, scale, t, color):
    inner = []
    if product == "zenoku":
        rlen = 2 * 3.141592653589793 * G.R
        q = ease_in_out_cubic(seg(t, 0.0, 1.0))
        inner.append(f'<circle {dash_attrs(rlen, q)} cx="{G.C}" cy="{G.C}" r="{G.R}" fill="none" stroke="{color}" stroke-width="{G.SW}"/>')
        dp = max(ease_out_back(seg(t, 0.85, 0.45)), 0.0)
        inner.append(f'<g transform="translate({G.C} {G.C}) scale({dp:.4f}) translate(-{G.C} -{G.C})"><circle cx="{G.C}" cy="{G.C}" r="4.0" fill="{color}"/></g>')
    else:
        q = ease_in_out_cubic(seg(t, 0.0, 1.0))
        inner.append(f'<path {dash_attrs(M._path_length(G.ARC), q)} d="{G.ARC}" fill="none" stroke="{color}" stroke-width="{G.SW}" stroke-linecap="round"/>')
        glyph = _annotated(G.GLYPHS[product](color, color), t, 0.45, 0.07, 0.85, color)
        inner.append(f'<g transform="translate({G.C} {G.C}) scale({G.GS}) translate(-{G.C} -{G.C})">\n{glyph}\n</g>')
    body = "\n".join(inner)
    return f'<g transform="translate({cx} {cy}) scale({scale}) translate(-32 -32)">\n{body}\n</g>'


def wordmark_group(product, cx, baseline, em, t, color):
    name = G.NAMES[product]
    p = ease_out_quint(seg(t, 0.72, 0.75))
    dy = 16 * (1 - p)
    mark, advance = G.text_to_path(name, 0, 0, em, color)
    return (f'<g opacity="{p:.4f}" transform="translate({cx - advance / 2:.2f} {baseline + dy:.2f})">\n'
            f'{mark}\n</g>')


def frame_product(product, t):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">
<rect width="{SIZE}" height="{SIZE}" fill="{INK}"/>
{mark_group(product, SIZE / 2, 430, 6.4, t, PAPER)}
{wordmark_group(product, SIZE / 2, 880, 92, t, PAPER)}
</svg>'''


GROUND = ["zeno", "zent", "rsh", "auth", "zenoku-dev"]


def frame_family(t):
    parts = [f'<rect width="{SIZE}" height="{SIZE}" fill="{INK}"/>']
    if t < 2.9:
        local = min(t / 2.5, 1.0)
        parts.append(mark_group("zenoku", SIZE / 2, 430, 6.4, local, PAPER))
        parts.append(wordmark_group("zenoku", SIZE / 2, 880, 92, local, PAPER))
    elif t < 7.6:
        # Фаза 2: пять знаков в сетке (строка из 3 + строка из 2)
        local = t - 2.9
        fade = ease_out_quint(seg(local, 0.0, 0.4))
        cells = [("zeno", 200, 300), ("zent", 540, 300), ("rsh", 880, 300),
                 ("auth", 370, 740), ("zenoku-dev", 710, 740)]
        parts.append(f'<g opacity="{fade:.4f}">')
        for i, (prod, cx, cy) in enumerate(cells):
            lt = local - i * 0.35
            if lt <= 0:
                continue
            lt = min(lt / 2.0, 1.0)
            parts.append(mark_group(prod, cx, cy - 30, 2.6, lt, PAPER))
            parts.append(wordmark_group(prod, cx, cy + 150, 40, lt, PAPER))
        parts.append('</g>')
    else:
        local = min((t - 7.6) / 1.4, 1.0)
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
    targets = sys.argv[1:] or ["zenoku", "zeno", "zent", "rsh", "auth", "zenoku-dev", "family"]
    for target in targets:
        if target == "family":
            render(int(10.9 * FPS), os.path.join(out_dir, "sting-family.mp4"), frame_family)
        else:
            render(int(4.2 * FPS), os.path.join(out_dir, f"sting-{target}.mp4"),
                   lambda t, p=target: frame_product(p, min(t / 2.6, 1.0)))


if __name__ == "__main__":
    main()
