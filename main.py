#!/usr/bin/env python3
"""NEWSVISION - one image summing up 25 November 2026 world news.

Pure Python 3.13 standard library: no network, no PIL, no system fonts.
Draws a 1024x1024 PNG with a small bitmap font implemented in code,
then writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Deterministic: identical bytes on every run.

Composition (after the reference image's deep-blue / teal / gold palette):
a clean headline band naming the day, a large drawn Earth at the centre,
and seven captioned panels for seven verified stories of 25 Nov 2026.
"""

import hashlib
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
INK = (5, 15, 28)        # near-black navy
NAVY = (8, 24, 40)
PANEL = (13, 44, 66)
PANEL_EDGE = (120, 96, 40)
GOLD = (232, 182, 76)
GOLD_DK = (168, 128, 48)
TEAL = (47, 212, 191)
TEAL_DK = (34, 140, 128)
SEA = (14, 75, 112)
SEA_LT = (28, 124, 162)
LAND = (53, 176, 138)
LAND_DK = (28, 118, 88)
WHITE = (240, 244, 248)
MIST = (170, 200, 215)
RED = (235, 87, 74)
SMOKE = (150, 160, 170)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, '1' = pixel on.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
BLANK = ("00000",) * 7


def text_width(s, scale):
    return len(s) * (5 * scale + scale) - scale


# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def _off(x, y):
    return (y * W + x) * 3


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        o = _off(x, y)
        buf[o], buf[o + 1], buf[o + 2] = color


def blend_px(x, y, color, alpha):
    if 0 <= x < W and 0 <= y < H:
        o = _off(x, y)
        buf[o] = int(buf[o] * (1 - alpha) + color[0] * alpha)
        buf[o + 1] = int(buf[o + 1] * (1 - alpha) + color[1] * alpha)
        buf[o + 2] = int(buf[o + 2] * (1 - alpha) + color[2] * alpha)


def rect(x, y, w, h, color):
    x0, x1 = max(0, x), min(W, x + w)
    y0, y1 = max(0, y), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        o = _off(x0, yy)
        buf[o:o + len(row)] = row


def rect_outline(x, y, w, h, color):
    rect(x, y, w, 1, color)
    rect(x, y + h - 1, w, 1, color)
    rect(x, y, 1, h, color)
    rect(x + w - 1, y, 1, h, color)


def hline(x0, x1, y, color):
    if 0 <= y < H:
        rect(min(x0, x1), y, abs(x1 - x0) + 1, 1, color)


def vline(x, y0, y1, color):
    if 0 <= x < W:
        rect(x, min(y0, y1), 1, abs(y1 - y0) + 1, color)


def line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def line2(x0, y0, x1, y1, color):
    line(x0, y0, x1, y1, color)
    line(x0 + 1, y0, x1 + 1, y1, color)


def disc(cx, cy, r, color, clip=None):
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        if abs(dy) > r:
            continue
        dx = int((r * r - dy * dy) ** 0.5)
        xa, xb = cx - dx, cx + dx
        if clip is not None:
            ccx, ccy, cr = clip
            ddy = y - ccy
            if abs(ddy) >= cr:
                continue
            ddx = int((cr * cr - ddy * ddy) ** 0.5)
            xa = max(xa, ccx - ddx)
            xb = min(xb, ccx + ddx)
        if xb >= xa:
            rect(xa, y, xb - xa + 1, 1, color)


def ring(cx, cy, r, color):
    x = 0
    y = r
    d = 3 - 2 * r
    while x <= y:
        for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                       (x, -y), (y, -x), (-x, -y), (-y, -x)):
            px(cx + sx, cy + sy, color)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1


def poly_fill(pts, color, clip=None):
    ys = [p[1] for p in pts]
    y0, y1 = min(ys), max(ys)
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                t = (y - ay) / (by - ay)
                xs.append(ax + t * (bx - ax))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa, xb = int(xs[i]), int(xs[i + 1])
            if clip is not None:
                ccx, ccy, cr = clip
                dy = y - ccy
                if abs(dy) >= cr:
                    continue
                dx = int((cr * cr - dy * dy) ** 0.5)
                xa = max(xa, ccx - dx)
                xb = min(xb, ccx + dx)
            if xb >= xa:
                rect(xa, y, xb - xa + 1, 1, color)


def poly_outline(pts, color):
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        line(x0, y0, x1, y1, color)


def bezier(p0, p1, p2, color, steps=40):
    prev = p0
    for i in range(1, steps + 1):
        t = i / steps
        x = int((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0])
        y = int((1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
        line(prev[0], prev[1], x, y, color)
        prev = (x, y)


def draw_text(x, y, s, scale, color, bold=False, align="left"):
    s = s.upper()  # the bitmap font carries capitals only
    w = text_width(s, scale)
    if align == "center":
        x = x - w // 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        glyph = FONT.get(ch, BLANK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    rect(cx + col * scale, y + row * scale, scale, scale, color)
                    if bold:
                        rect(cx + col * scale + 1, y + row * scale, scale, scale, color)
        cx += 5 * scale + scale
    return w


# ---------------------------------------------------------------- background
def draw_background():
    stops = [(0.0, (5, 15, 28)), (0.45, (12, 47, 75)), (1.0, (4, 16, 29))]
    for band in range(0, H, 4):
        t = band / H
        if t < stops[1][0]:
            a, b = stops[0], stops[1]
            f = t / stops[1][0]
        else:
            a, b = stops[1], stops[2]
            f = (t - stops[1][0]) / (1 - stops[1][0])
        c = tuple(int(a[1][i] + (b[1][i] - a[1][i]) * f) for i in range(3))
        rect(0, band, W, 4, c)
    # faint network dots and links, upper corners
    dots = [(70, 180), (150, 150), (240, 210), (880, 170), (950, 240),
            (90, 830), (170, 880), (860, 860), (940, 800), (60, 420),
            (970, 470), (40, 620), (990, 640)]
    for (dx, dy) in dots:
        disc(dx, dy, 2, TEAL_DK)
    for (a, b) in [((70, 180), (150, 150)), ((150, 150), (240, 210)),
                   ((880, 170), (950, 240)), ((90, 830), (170, 880)),
                   ((860, 860), (940, 800))]:
        x0, y0 = a
        x1, y1 = b
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            blend_px(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t),
                     TEAL, 0.25)


# ---------------------------------------------------------------- headline
def draw_headline():
    draw_text(W // 2, 16, "ONE PLANET. ONE DAY.", 3, GOLD, bold=True, align="center")
    draw_text(W // 2, 48, "A THOUSAND STORIES.", 3, GOLD, bold=True, align="center")
    # gold date pill, centred and prominent
    label = "NOVEMBER 25, 2026"
    lw = text_width(label, 2)
    px0 = W // 2 - lw // 2 - 18
    py0 = 84
    rect(px0, py0, lw + 36, 28, (10, 30, 50))
    rect_outline(px0, py0, lw + 36, 28, GOLD)
    draw_text(W // 2, py0 + 7, label, 2, GOLD, bold=True, align="center")
    hline(0, W - 1, 124, GOLD_DK)
    hline(0, W - 1, 128, (60, 46, 16))


# ---------------------------------------------------------------- the Earth
GCX, GCY, GR = 512, 492, 185


def _g(fx, fy):
    return (int(GCX + fx * GR), int(GCY + fy * GR))


def draw_globe():
    # stepped glow around the globe
    for r, c in ((258, (10, 40, 60)), (240, (12, 48, 72)),
                 (222, (14, 56, 84)), (205, (16, 64, 94))):
        disc(GCX, GCY, r, c)
    # ocean
    disc(GCX, GCY, GR, SEA)
    # soft light from the upper left, clipped to the globe, stepped
    for r, c in ((84, (18, 92, 134)), (62, (22, 108, 150)),
                 (40, (26, 124, 162))):
        disc(GCX - 58, GCY - 66, r, c, clip=(GCX, GCY, GR))
    # graticule, faint
    for dy in (-92, 0, 92):
        y = GCY + dy
        dx = int((GR * GR - dy * dy) ** 0.5)
        for x in range(GCX - dx, GCX + dx + 1):
            blend_px(x, y, WHITE, 0.10)
    for dx in (-92, 92):
        x = GCX + dx
        dy = int((GR * GR - dx * dx) ** 0.5)
        for y in range(GCY - dy, GCY + dy + 1):
            blend_px(x, y, WHITE, 0.10)
    # continents (Americas centred, Africa and Europe at the right edge)
    clip = (GCX, GCY, GR)
    north_america = [(-0.99, -0.30), (-0.92, -0.52), (-0.78, -0.72),
                     (-0.62, -0.88), (-0.42, -0.84), (-0.30, -0.68),
                     (-0.14, -0.60), (-0.04, -0.48), (-0.16, -0.40),
                     (-0.30, -0.34), (-0.24, -0.22), (-0.34, -0.10),
                     (-0.50, -0.06), (-0.58, -0.20), (-0.72, -0.22),
                     (-0.88, -0.18)]
    greenland = [(0.00, -0.94), (0.14, -0.92), (0.18, -0.80),
                 (0.06, -0.74), (-0.06, -0.82)]
    south_america = [(-0.52, 0.02), (-0.36, 0.00), (-0.24, 0.08),
                     (-0.16, 0.24), (-0.24, 0.44), (-0.36, 0.64),
                     (-0.48, 0.72), (-0.54, 0.52), (-0.56, 0.30),
                     (-0.60, 0.14)]
    africa = [(0.52, -0.52), (0.72, -0.46), (0.86, -0.28), (0.88, -0.06),
              (0.74, 0.06), (0.60, 0.02), (0.52, -0.20)]
    europe = [(0.50, -0.78), (0.68, -0.84), (0.84, -0.70),
              (0.78, -0.56), (0.60, -0.58)]
    for poly in (north_america, greenland, south_america, africa, europe):
        pts = [_g(fx, fy) for fx, fy in poly]
        poly_fill(pts, LAND, clip=clip)
        poly_outline(pts, LAND_DK)
    # city dots
    for fx, fy in ((-0.45, -0.35), (-0.30, 0.30), (0.65, -0.30),
                   (-0.62, -0.12)):
        x, y = _g(fx, fy)
        disc(x, y, 3, GOLD)
        disc(x, y, 1, WHITE)
    # glowing rim
    ring(GCX, GCY, GR, TEAL)
    ring(GCX, GCY, GR + 2, TEAL_DK)
    ring(GCX, GCY, GR + 5, (20, 90, 84))
    # gold route arcs with end nodes
    routes = [((-0.72, -0.52), (-0.05, -1.05), (0.62, -0.34)),
              ((-0.42, 0.52), (0.10, 0.92), (0.72, 0.18)),
              ((-0.82, 0.08), (-0.20, -0.28), (0.48, -0.68))]
    for a, c, b in routes:
        bezier(_g(*a), _g(*c), _g(*b), GOLD)
        for fx, fy in (a, b):
            x, y = _g(fx, fy)
            disc(x, y, 4, GOLD)
            disc(x, y, 2, WHITE)


# ---------------------------------------------------------------- icons
def icon_ship(ox, oy):
    # sea
    for dx in range(0, 64, 8):
        line(ox + dx, oy + 58, ox + dx + 5, oy + 58, TEAL_DK)
    # hull
    poly_fill([(ox + 6, oy + 42), (ox + 58, oy + 42), (ox + 50, oy + 56),
               (ox + 14, oy + 56)], GOLD)
    rect(ox + 30, oy + 30, 14, 12, GOLD_DK)
    vline(ox + 37, oy + 18, oy + 30, WHITE)
    line(ox + 37, oy + 18, ox + 48, oy + 24, WHITE)
    # drone above
    line(ox + 8, oy + 6, ox + 16, oy + 14, WHITE)
    line(ox + 16, oy + 6, ox + 8, oy + 14, WHITE)
    disc(ox + 12, oy + 10, 2, GOLD)


def icon_skyline(ox, oy):
    rect(ox + 4, oy + 26, 14, 32, MIST)
    rect(ox + 22, oy + 14, 16, 44, (140, 165, 180))
    rect(ox + 42, oy + 30, 14, 28, MIST)
    for wx in (8, 26, 46):
        for wy in (30, 38, 46):
            disc(ox + wx, oy + wy, 1, GOLD)
    # smoke puffs
    disc(ox + 30, oy + 8, 6, SMOKE)
    disc(ox + 40, oy + 4, 5, SMOKE)
    disc(ox + 50, oy + 10, 4, SMOKE)


def icon_tower(ox, oy):
    poly_fill([(ox + 26, oy + 58), (ox + 29, oy + 10), (ox + 35, oy + 10),
               (ox + 38, oy + 58)], GOLD)
    for yy in (20, 30, 40, 50):
        hline(ox + 28, ox + 36, oy + yy, GOLD_DK)
    vline(ox + 32, oy + 2, oy + 10, WHITE)
    disc(ox + 44, oy + 14, 6, SMOKE)
    disc(ox + 52, oy + 8, 5, SMOKE)
    disc(ox + 40, oy + 18, 2, RED)


def icon_chart(ox, oy):
    line(ox + 8, oy + 6, ox + 8, oy + 52, WHITE)
    line(ox + 8, oy + 52, ox + 58, oy + 52, WHITE)
    line2(ox + 10, oy + 14, ox + 22, oy + 22, RED)
    line2(ox + 22, oy + 22, ox + 32, oy + 20, RED)
    line2(ox + 32, oy + 20, ox + 44, oy + 36, RED)
    line2(ox + 44, oy + 36, ox + 54, oy + 48, RED)
    line(ox + 54, oy + 48, ox + 48, oy + 48, RED)
    line(ox + 54, oy + 48, ox + 54, oy + 42, RED)


def icon_court(ox, oy):
    poly_fill([(ox + 6, oy + 26), (ox + 32, oy + 10), (ox + 58, oy + 26)], GOLD)
    rect(ox + 6, oy + 26, 52, 5, GOLD_DK)
    for cx in (12, 24, 36, 48):
        rect(ox + cx, oy + 33, 4, 19, WHITE)
    rect(ox + 4, oy + 52, 56, 5, WHITE)


def icon_summit(ox, oy):
    # round table with empty chairs, cracked earth below
    rect(ox + 8, oy + 30, 48, 5, (90, 110, 125))
    rect(ox + 30, oy + 35, 4, 16, (90, 110, 125))
    for cx in (8, 24, 44, 56):
        rect(ox + cx, oy + 40, 6, 14, MIST)
    disc(ox + 32, oy + 22, 9, GOLD)
    line(ox + 2, oy + 60, ox + 18, oy + 54, RED)
    line(ox + 18, oy + 54, ox + 34, oy + 60, RED)
    line(ox + 34, oy + 60, ox + 48, oy + 54, RED)
    line(ox + 48, oy + 54, ox + 62, oy + 60, RED)


def icon_probe(ox, oy):
    poly_fill([(ox + 8, oy + 26), (ox + 24, oy + 12), (ox + 40, oy + 26)], GOLD)
    rect(ox + 8, oy + 26, 32, 5, GOLD_DK)
    for cx in (12, 22, 32):
        rect(ox + cx, oy + 33, 4, 23, WHITE)
    rect(ox + 6, oy + 56, 36, 4, WHITE)
    ring(ox + 50, oy + 18, 10, WHITE)
    ring(ox + 50, oy + 18, 9, WHITE)
    line(ox + 57, oy + 25, ox + 63, oy + 31, WHITE)


# ---------------------------------------------------------------- panels
def draw_panel(x, y, w, h, tag, headline, sub, icon):
    rect(x, y, w, h, PANEL)
    rect_outline(x, y, w, h, PANEL_EDGE)
    # tag bar
    rect(x, y, w, 24, GOLD)
    draw_text(x + w // 2, y + 8, tag, 1, NAVY, bold=True, align="center")
    # icon, centred
    icon(x + (w - 64) // 2, y + 36)
    # headline, two lines, bold white
    draw_text(x + w // 2, y + 112, headline[0], 2, WHITE, bold=True, align="center")
    draw_text(x + w // 2, y + 130, headline[1], 2, WHITE, bold=True, align="center")
    # sub-line, two lines, mist
    draw_text(x + w // 2, y + 158, sub[0], 1, MIST, align="center")
    draw_text(x + w // 2, y + 169, sub[1], 1, MIST, align="center")


def draw_panels():
    left_x, right_x = 20, 728
    pw, ph = 276, 212
    ys = (140, 368, 596)
    # left column: Ukraine, Gaza, Riyadh
    draw_panel(left_x, ys[0], pw, ph, "UKRAINE - BALTIC",
               ("UKRAINE DRONES", "HIT RUSSIAN SHIPS"),
               ("Zelenskiy confirms drone strike",
                "on Russian ship, Gulf of Finland"),
               icon_ship)
    draw_panel(left_x, ys[1], pw, ph, "GAZA",
               ("GAZA STRIKE KILLS", "HAMAS OFFICIAL"),
               ("Israeli strike kills Hamas",
                "official in Gaza"),
               icon_skyline)
    draw_panel(left_x, ys[2], pw, ph, "SAUDI ARABIA",
               ("HOUTHIS HIT", "RIYADH TOWER"),
               ("Strike hits Riyadh's tallest",
                "tower; 11 wounded, officials say"),
               icon_tower)
    # right column: markets, Huawei, China
    draw_panel(right_x, ys[0], pw, ph, "MARKETS",
               ("ASIA MARKETS", "TUMBLE"),
               ("Kospi -5.6%, Taiex -6%, Nikkei -3.6%",
                "after fresh US tariff threats"),
               icon_chart)
    draw_panel(right_x, ys[1], pw, ph, "TECH - US COURT",
               ("HUAWEI FOUND", "GUILTY"),
               ("Brooklyn jury: guilty of trade",
                "secret theft and bank fraud"),
               icon_court)
    draw_panel(right_x, ys[2], pw, ph, "CHINA",
               ("CHINA PROBES", "SHANGHAI CHIEF"),
               ("Beijing probes Shanghai party",
                "chief Chen Jining, Politburo"),
               icon_probe)


def draw_bottom():
    x, y, w, h = 20, 860, 984, 140
    rect(x, y, w, h, PANEL)
    rect_outline(x, y, w, h, PANEL_EDGE)
    # tag chip
    rect(x + 16, y + 14, 92, 22, GOLD)
    draw_text(x + 62, y + 21, "CLIMATE", 1, NAVY, bold=True, align="center")
    # summit icon
    icon_summit(x + 128, y + 26)
    # headline + sub-line
    draw_text(x + 216, y + 34, "COP31 TALKS COLLAPSE", 2, WHITE, bold=True)
    draw_text(x + 216, y + 62,
              "UN summit in Antalya ends with no final agreement",
              1, MIST)
    draw_text(x + 216, y + 76,
              "as oil states block fossil-fuel phaseout language",
              1, MIST)
    # domed capitol skyline at the right, echoing the reference image
    bx = x + 736
    by = y + 22
    poly_fill([(bx, by + 52), (bx + 28, by + 14), (bx + 56, by + 52)], GOLD_DK)
    rect(bx + 4, by + 52, 48, 26, GOLD_DK)
    for cx in (bx + 10, bx + 22, bx + 34, bx + 44):
        rect(cx, by + 58, 3, 20, GOLD)
    rect(bx + 64, by + 36, 34, 42, GOLD_DK)
    poly_fill([(bx + 64, by + 36), (bx + 81, by + 22), (bx + 98, by + 36)], GOLD_DK)
    rect(bx + 106, by + 46, 40, 32, GOLD_DK)
    draw_text(x + 736, y + 116, "GOVERNMENTS  MARKETS  PEOPLE", 1, GOLD,
              align="left")


# ---------------------------------------------------------------- PNG output
def write_png(path):
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    comp = zlib.compress(raw, 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    draw_background()
    draw_globe()
    draw_headline()
    draw_panels()
    draw_bottom()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%dx%d, %d bytes, sha256 %s)" % (path, W, H, size, digest))


if __name__ == "__main__":
    main()
