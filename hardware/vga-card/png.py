"""
Minimal PNG reader/writer (standard library only, so no Pillow needed).

read_png(path)  -> (width, height, rows)   rows[y][x] = (r, g, b)
write_png(path, width, height, rows)

Supports what image editors normally save: 8-bit greyscale, RGB, RGBA,
grey+alpha and palette images, non-interlaced. A PNG is a signature plus
chunks; the pixels live in IDAT chunks as zlib-compressed scanlines, and
each scanline starts with a 'filter' byte saying how it was predicted
from its neighbours (the decoder has to undo that).
"""
import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}   # colour type -> samples per pixel


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path):
    data = open(path, "rb").read()
    if not data.startswith(SIGNATURE):
        raise ValueError(f"{path} is not a PNG")
    pos, idat, palette = 8, b"", None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if depth != 8 or interlace:
        raise ValueError("only 8-bit, non-interlaced PNGs are supported")

    bpp = CHANNELS[ctype]
    stride = width * bpp
    raw = zlib.decompress(idat)
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        ftype, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            pred = (0, a, b, (a + b) // 2, _paeth(a, b, c))[ftype]
            line[i] = (line[i] + pred) & 0xFF
        prev = line
        row = []
        for x in range(width):
            px = line[x * bpp:(x + 1) * bpp]
            if ctype == 3:
                row.append(palette[px[0]])
            elif ctype in (0, 4):
                row.append((px[0],) * 3)
            else:
                row.append(tuple(px[:3]))
        rows.append(row)
    return width, height, rows


def write_png(path, width, height, rows):
    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rows)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    with open(path, "wb") as f:
        f.write(SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
