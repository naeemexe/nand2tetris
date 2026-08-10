#!/usr/bin/env python3
"""
Turn a picture into the VGA card's image EEPROM (28C256).

    python3 image_to_rom.py photo.png             # any 8-bit PNG
    python3 image_to_rom.py --test-pattern        # built-in pattern, no file needed
    options: --dither   ordered (Bayer) dithering, looks better with only 64 colours

Writes:
    build/image.bin               32 KB raw EEPROM image
    build/preview.png             the 100x75 image blown up 8x, exactly as it will look
    ../eeprom-programmer/eeprom_programmer/vga_image.h   Arduino header (first 9600 bytes)

Steps:
  1. crop the picture to 4:3 (the shape of 800x600), centred
  2. shrink to 100 x 75 by averaging each block of source pixels
  3. reduce each channel to 2 bits (4 levels) -> 4 x 4 x 4 = 64 colours
  4. pack as one byte per pixel:  bits 5..4 red, 3..2 green, 1..0 blue
     at address y * 128 + x   (x 100..127 is never shown, left 0)
"""
import argparse
import math
from pathlib import Path

from png import read_png, write_png
from vga_timing import IMAGE_W, IMAGE_H

ROM_SIZE = 32768
HERE = Path(__file__).parent

# 4x4 Bayer matrix: spreads the rounding error into a fine regular pattern.
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def crop_43(width, height, rows):
    if width * 3 > height * 4:                  # too wide: trim the sides
        new_w = height * 4 // 3
        left = (width - new_w) // 2
        return new_w, height, [row[left:left + new_w] for row in rows]
    new_h = width * 3 // 4                      # too tall: trim top and bottom
    top = (height - new_h) // 2
    return width, new_h, rows[top:top + new_h]


def downscale(width, height, rows, out_w, out_h):
    """Box filter: each output pixel is the average of the source pixels it covers."""
    out = []
    for oy in range(out_h):
        y0, y1 = oy * height // out_h, max((oy + 1) * height // out_h, oy * height // out_h + 1)
        row = []
        for ox in range(out_w):
            x0, x1 = ox * width // out_w, max((ox + 1) * width // out_w, ox * width // out_w + 1)
            block = [rows[y][x] for y in range(y0, y1) for x in range(x0, x1)]
            row.append(tuple(sum(p[c] for p in block) / len(block) for c in range(3)))
        out.append(row)
    return out


def quantize(value, x, y, dither):
    """0..255 -> 0..3."""
    level = value / 255 * 3
    if dither:
        level += (BAYER[y % 4][x % 4] + 0.5) / 16 - 0.5
    return min(3, max(0, round(level)))


def test_pattern():
    """100x75: colour bars on top, a grey ramp, then a circle over a hue gradient."""
    rows = []
    bars = [(3, 3, 3), (3, 3, 0), (0, 3, 3), (0, 3, 0), (3, 0, 3), (3, 0, 0), (0, 0, 3), (0, 0, 0)]
    for y in range(IMAGE_H):
        row = []
        for x in range(IMAGE_W):
            if y < 25:
                px = bars[x * 8 // IMAGE_W]
            elif y < 32:
                g = x * 4 // IMAGE_W
                px = (g, g, g)
            else:
                inside = (x - 50) ** 2 + (y - 53) ** 2 < 18 ** 2
                hue = x / IMAGE_W * 2 * math.pi
                px = (3, 3, 3) if inside else tuple(
                    round(1.5 + 1.5 * math.cos(hue - k * 2 * math.pi / 3)) for k in range(3))
            row.append(tuple(c * 85 for c in px))
        rows.append(row)
    return rows


def to_rom(pixels, dither=False) -> bytes:
    rom = bytearray(ROM_SIZE)
    for y in range(IMAGE_H):
        for x in range(IMAGE_W):
            r, g, b = (quantize(v, x, y, dither) for v in pixels[y][x])
            rom[y * 128 + x] = (r << 4) | (g << 2) | b
    return bytes(rom)


def rom_pixel_rgb(byte) -> tuple:
    """What the DAC makes of a ROM byte, as 0..255 RGB (for previews)."""
    return ((byte >> 4 & 3) * 85, (byte >> 2 & 3) * 85, (byte & 3) * 85)


def write_preview(rom, path, scale=8):
    rows = []
    for y in range(IMAGE_H):
        row = [rom_pixel_rgb(rom[y * 128 + x]) for x in range(IMAGE_W) for _ in range(scale)]
        rows.extend([row] * scale)
    write_png(path, IMAGE_W * scale, IMAGE_H * scale, rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?")
    p.add_argument("--test-pattern", action="store_true")
    p.add_argument("--dither", action="store_true")
    args = p.parse_args()
    if args.test_pattern or not args.image:
        pixels = test_pattern()
    else:
        w, h, rows = read_png(args.image)
        w, h, rows = crop_43(w, h, rows)
        pixels = downscale(w, h, rows, IMAGE_W, IMAGE_H)

    rom = to_rom(pixels, args.dither)
    build = HERE / "build"
    build.mkdir(exist_ok=True)
    (build / "image.bin").write_bytes(rom)
    write_preview(rom, build / "preview.png")

    used = IMAGE_H * 128                       # the rest of the chip is never addressed while visible
    import sys
    sys.path.insert(0, str(HERE.parent / "8bit-computer"))
    from microcode import c_header
    sketch = HERE.parent / "eeprom-programmer" / "eeprom_programmer"
    (sketch / "vga_image.h").write_text(c_header(rom[:used], "vga image"))
    print(f"wrote build/image.bin, build/preview.png, ../eeprom-programmer/eeprom_programmer/vga_image.h "
          f"({len(set(rom[:used]))} distinct colours used)")


if __name__ == "__main__":
    main()
