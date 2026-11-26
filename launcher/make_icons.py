"""make_icons.py - draws the two Windows icons of the bundle (no extra Python packages needed).

  oss_flow.ico      OSS Flow window: blue tile with a white digital waveform
  oss_terminal.ico  OSS Flow Terminal: dark tile with a green  >_  prompt

Each .ico holds PNG images of 16, 20, 24, 32, 40, 48, 64 and 256 px, so Windows picks a sharp one at every
display scaling (100 % ... 250 %). Run:  python make_icons.py   (writes the files next to this script)
"""
import math
import struct
import zlib
from pathlib import Path

SIZES = (16, 20, 24, 32, 40, 48, 64, 256)


def rounded_box(x, y, r):
    """Inside the tile (unit square with rounded corners of radius r)?"""
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def near_polyline(x, y, pts, w):
    """Within w/2 of the polyline pts (thick line with round joints)?"""
    h2 = (w / 2) ** 2
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        if (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2 <= h2:
            return True
    return False


def blend(dst, src, a):
    return tuple(d + (s - d) * a for d, s in zip(dst, src))


def draw(size, layers):
    """layers: list of (test(x, y) -> bool, (r, g, b) or function(y) -> (r, g, b)). Returns RGBA rows."""
    ss = 4 if size <= 64 else 3                       # supersampling for smooth edges
    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(ss):
                for sx in range(ss):
                    x = (px + (sx + 0.5) / ss) / size
                    y = (py + (sy + 0.5) / ss) / size
                    col, a = (0.0, 0.0, 0.0), 0.0
                    for test, paint in layers:
                        if test(x, y):
                            c = paint(y) if callable(paint) else paint
                            col, a = (c if a == 0 else blend(col, c, 1.0)), 1.0
                    acc[0] += col[0] * a
                    acc[1] += col[1] * a
                    acc[2] += col[2] * a
                    acc[3] += a
            n = ss * ss
            alpha = acc[3] / n
            if alpha > 0:
                row += bytes((round(acc[0] / acc[3]), round(acc[1] / acc[3]), round(acc[2] / acc[3]),
                              round(alpha * 255)))
            else:
                row += b"\0\0\0\0"
        rows.append(bytes(row))
    return rows


def png(size, rows):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = b"".join(b"\0" + r for r in rows)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def ico(images):
    head = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    dirs, data = b"", b""
    for size, blob in images:
        s = 0 if size >= 256 else size
        dirs += struct.pack("<BBBBHHII", s, s, 0, 0, 1, 32, len(blob), offset + len(data))
        data += blob
    return head + dirs + data


def flow_layers(size):
    r = 0.2
    w = max(0.085, 1.6 / size)                       # line at least ~1.6 px wide on tiny icons
    wave = [(0.14, 0.62), (0.30, 0.62), (0.30, 0.34), (0.50, 0.34), (0.50, 0.62), (0.70, 0.62),
            (0.70, 0.34), (0.86, 0.34)]
    tick = [(0.14, 0.80), (0.86, 0.80)]
    return [(lambda x, y: rounded_box(x, y, r), lambda y: blend((43, 108, 176), (26, 64, 122), y)),
            (lambda x, y: near_polyline(x, y, tick, w * 0.55), (125, 211, 252)),
            (lambda x, y: near_polyline(x, y, wave, w), (255, 255, 255))]


def terminal_layers(size):
    r = 0.2
    w = max(0.1, 1.8 / size)
    chevron = [(0.22, 0.30), (0.44, 0.50), (0.22, 0.70)]
    under = [(0.52, 0.70), (0.78, 0.70)]
    return [(lambda x, y: rounded_box(x, y, r), lambda y: blend((45, 45, 48), (20, 20, 22), y)),
            (lambda x, y: near_polyline(x, y, chevron, w), (106, 212, 106)),
            (lambda x, y: near_polyline(x, y, under, w), (230, 230, 230))]


def main():
    here = Path(__file__).resolve().parent
    for name, layers in (("oss_flow.ico", flow_layers), ("oss_terminal.ico", terminal_layers)):
        images = [(s, png(s, draw(s, layers(s)))) for s in SIZES]
        (here / name).write_bytes(ico(images))
        print("wrote", here / name, sum(len(b) for _, b in images), "bytes of PNG data")


if __name__ == "__main__":
    main()
