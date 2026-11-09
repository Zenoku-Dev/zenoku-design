#!/bin/sh
# Пересобрать SVG и экспортировать PNG. Нужен python3 и rsvg-convert.
set -e
cd "$(dirname "$0")/.."

python3 scripts/generate_svg.py

for p in zenoku zeno zent rsh auth; do
  d="assets/$p"
  mkdir -p "$d/png"
  rsvg-convert -w 512  "$d/mark.svg"    -o "$d/png/mark-512.png"
  rsvg-convert -w 1024 "$d/mark.svg"    -o "$d/png/mark-1024.png"
  rsvg-convert -w 1600 "$d/logo.svg"    -o "$d/png/logo-1600.png"
  rsvg-convert -w 1600 "$d/logo-dark.svg" -o "$d/png/logo-dark-1600.png"
  rsvg-convert -w 512  "$d/app-icon.svg" -o "$d/png/app-icon-512.png"
  rsvg-convert -w 1024 "$d/app-icon.svg" -o "$d/png/app-icon-1024.png"
  rsvg-convert --height 1024 "$d/readme-banner.svg"      -o "$d/png/readme-banner.png"
  rsvg-convert --height 1024 "$d/readme-banner-dark.svg" -o "$d/png/readme-banner-dark.png"
  for s in 16 32 48 180 192 512; do
    rsvg-convert -w "$s" "$d/favicon.svg" -o "$d/png/favicon-$s.png"
  done
done
echo "png ok"
