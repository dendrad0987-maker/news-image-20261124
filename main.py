#!/usr/bin/env python3
"""Draw a newspaper front page summing up 24 November 2026.

Pure standard library. No network, no files read, no randomness:
two runs write identical bytes. Writes entry.png to
$MAKEFUN_OUTPUT_DIR (default /output).
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (246, 241, 227)
WHITE = (255, 255, 255)
INK = (17, 17, 17)
RED = (180, 35, 24)
BLUE = (29, 78, 137)
GREEN = (30, 122, 52)
ORANGE = (232, 106, 23)
GOLD = (201, 162, 39)
GREY = (90, 90, 90)
LIGHT = (226, 219, 198)
SKY = (214, 231, 240)
SEA = (46, 110, 168)

# 5x7 bitmap font, '#' = ink. Only the characters the page uses.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '*': ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def frame(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if abs(d - r) <= t / 2:
                    self.set(xx, yy, c)

    def triangle(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            nodes = []
            for i in range(3):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % 3]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    nodes.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                for xx in range(int(nodes[i]), int(nodes[i + 1]) + 1):
                    self.set(xx, yy, c)


def text_w(s, scale, gap=1):
    return len(s) * (5 * scale + gap) - gap if s else 0


def draw_text(cv, x, y, s, scale, c, gap=1):
    for ch in s:
        glyph = FONT.get(ch.upper(), FONT['?'])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '1':
                    cv.rect(x + col * scale, y + row * scale, scale, scale, c)
        x += 5 * scale + gap
    return x


def draw_centred(cv, cx, y, s, scale, c):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap_lines(s, scale, max_w, gap=1):
    words, lines, cur = s.split(' '), [], ''
    cw = 5 * scale + gap
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if len(trial) * cw - gap <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, y, s, scale, c, max_w, line_h):
    for line in wrap_lines(s, scale, max_w):
        draw_text(cv, x, y, line, scale, c)
        y += line_h
    return y


# ---- illustrations (flat, drawn shapes only) ----

def draw_globe(cv, cx, cy, r):
    cv.disc(cx, cy, r, BLUE)
    cv.disc(cx - r // 3, cy - r // 4, r // 4, GREEN)
    cv.disc(cx + r // 3, cy + r // 3, r // 5, GREEN)
    cv.disc(cx + r // 5, cy - r // 2, r // 6, GREEN)
    cv.ring(cx, cy, r, INK, 4)
    cv.line(cx - r, cy, cx + r, cy, LIGHT, 2)
    cv.line(cx, cy - r, cx, cy + r, LIGHT, 2)


def draw_ship(cv, x, y, w):
    # hull, cabin, mast, waves and flame at the stern
    cv.triangle([(x, y + 34), (x + w, y + 34), (x + w - 18, y + 62),
                 ], INK) if False else None
    cv.rect(x + 8, y + 34, w - 16, 26, INK)
    cv.triangle([(x + 8, y + 34), (x + w - 8, y + 34), (x + w - 30, y + 60)], INK)
    cv.rect(x + w // 2 - 8, y + 8, 26, 26, WHITE)
    cv.frame(x + w // 2 - 8, y + 8, 26, 26, INK, 2)
    cv.vline(x + w // 2 + 18, y - 14, 48, INK, 3)
    cv.triangle([(x + 6, y + 6), (x + 26, y + 16), (x + 6, y + 26)], ORANGE)
    cv.triangle([(x + 20, y + 12), (x + 34, y + 20), (x + 20, y + 28)], RED)
    for i in range(4):
        cv.disc(x + 14 + i * 30, y + 72, 12, SEA)
        cv.disc(x + 28 + i * 30, y + 72, 12, WHITE)


def draw_chart(cv, x, y, w, h):
    cv.rect(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK, 2)
    cv.vline(x + 14, y + 10, h - 24, INK, 2)
    cv.hline(x + 14, y + h - 14, w - 28, INK, 2)
    pts = [(x + 22, y + h - 30), (x + 48, y + h - 46), (x + 72, y + h - 38),
           (x + 96, y + h - 58), (x + 118, y + h - 76), (x + 138, y + h - 92)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], GREEN, 5)
    cv.triangle([(pts[-1][0] - 4, pts[-1][1] - 12), (pts[-1][0] + 14, pts[-1][1] - 4),
                 (pts[-1][0] - 2, pts[-1][1] + 6)], GREEN)


def draw_chess(cv, x, y, size):
    sq = size // 8
    for r in range(8):
        for c in range(8):
            col = WHITE if (r + c) % 2 == 0 else INK
            cv.rect(x + c * sq, y + r * sq, sq, sq, col)
    cv.frame(x, y, size, size, INK, 2)
    # white king on the left, black king on the right
    cv.disc(x + 2 * sq + sq // 2, y + 2 * sq + sq // 2, sq // 2 - 2, WHITE)
    cv.triangle([(x + 2 * sq + 4, y + 2 * sq + sq - 4),
                 (x + 3 * sq - 4, y + 2 * sq + sq - 4),
                 (x + 2 * sq + sq // 2, y + 2 * sq + 2)], GOLD)
    cv.disc(x + 5 * sq + sq // 2, y + 5 * sq + sq // 2, sq // 2 - 2, INK)
    cv.triangle([(x + 5 * sq + 4, y + 5 * sq + sq - 4),
                 (x + 6 * sq - 4, y + 5 * sq + sq - 4),
                 (x + 5 * sq + sq // 2, y + 5 * sq + 2)], GOLD)


def draw_factory(cv, x, y, w, h):
    cv.rect(x, y + h - 46, w, 46, INK)
    cv.rect(x + 10, y + 4, 16, 44, INK)
    cv.rect(x + 34, y + 14, 16, 34, INK)
    for fx, fy, s in ((x + 14, y - 6, 16), (x + 38, y + 2, 14),
                      (x + 66, y + 18, 20), (x + 92, y + 8, 16)):
        cv.triangle([(fx, fy + s), (fx + s // 2, fy), (fx + s, fy + s)], ORANGE)
        cv.triangle([(fx + 4, fy + s), (fx + s // 2, fy + 6), (fx + s - 4, fy + s)], RED)
    cv.rect(x + w - 44, y + h - 30, 26, 14, GOLD)


def draw_ballot(cv, x, y, w, h):
    cv.rect(x + 18, y + h - 34, w - 36, 34, INK)
    cv.rect(x + 4, y + h - 44, w - 8, 10, INK)
    cv.rect(x + w // 2 - 22, y + h - 48, 44, 4, PAPER)
    cv.rect(x + w // 2 - 14, y + 6, 28, 52, WHITE)
    cv.frame(x + w // 2 - 14, y + 6, 28, 52, INK, 2)
    cv.line(x + w // 2 - 14, y + 6, x + w // 2 + 14, y + 58, RED, 4)
    cv.line(x + w // 2 + 14, y + 6, x + w // 2 - 14, y + 58, RED, 4)


def draw_football(cv, x, y, r):
    cv.disc(x, y, r, WHITE)
    cv.ring(x, y, r, INK, 3)
    cv.disc(x, y, r // 3, INK)
    for ang in range(0, 360, 72):
        import math
        rad = math.radians(ang)
        cv.line(x, y, x + int(r * 0.95 * math.cos(rad)),
                y + int(r * 0.95 * math.sin(rad)), INK, 2)


# ---- page ----

def panel(cv, x, y, w, h, kicker, headline, deck, art):
    cv.rect(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK, 2)
    tx = x + 16
    draw_text(cv, tx, y + 14, kicker, 2, RED)
    cv.hline(tx, y + 34, w - 32, LIGHT, 2)
    hy = y + 44
    for line in headline:
        draw_text(cv, tx, hy, line, 3, INK)
        hy += 28
    draw_wrapped(cv, tx, hy + 6, deck, 2, INK, w - 32 - 118, 20)
    art(x + w - 132, y + 44, 116, h - 60)


def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(0, 0, W, 12, INK)
    # masthead
    draw_centred(cv, W // 2, 30, "THE WORLD", 12, INK)
    cv.hline(24, 128, W - 48, INK, 3)
    cv.hline(24, 134, W - 48, INK, 1)
    draw_centred(cv, W // 2, 146, "TUESDAY, 24 NOVEMBER 2026", 3, INK)
    draw_centred(cv, W // 2, 176, "SIX STORIES FROM AROUND THE WORLD", 2, GREY)

    # lead story: COP31
    lx, ly, lw, lh = 24, 200, W - 48, 224
    cv.rect(lx, ly, lw, lh, WHITE)
    cv.frame(lx, ly, lw, lh, INK, 3)
    draw_text(cv, lx + 20, ly + 16, "CLIMATE  *  ANTALYA, TURKIYE", 2, RED)
    draw_text(cv, lx + 20, ly + 48, "CLIMATE TALKS", 5, INK)
    draw_text(cv, lx + 20, ly + 92, "END WITH", 5, INK)
    draw_text(cv, lx + 20, ly + 136, "NO DEAL", 5, RED)
    draw_wrapped(cv, lx + 20, ly + 180, "COP31 closes with no agreed final text after a split over fossil fuels, a first in 17 years.", 2, INK, 540, 20)
    draw_globe(cv, lx + lw - 130, ly + 104, 78)
    cv.rect(lx + lw - 236, ly + 168, 212, 30, RED)
    draw_centred(cv, lx + lw - 130, ly + 175, "NO AGREEMENT", 2, WHITE)

    # grid of five stories + locator panel
    gx, gy = 24, 440
    pw, ph, gap = 476, 178, 12
    panel(cv, gx, gy, pw, ph, "WAR * LIBYA AND UKRAINE",
          ["SHIP SUNK", "OFF LIBYA"],
          "Ukrainian drones sank the Russian corvette Merkury at Benghazi. Strike kills 11.",
          lambda ax, ay, aw, ah: draw_ship(cv, ax, ay + 44, 112))
    panel(cv, gx + pw + gap, gy, pw, ph, "MARKETS * NEW YORK",
          ["HUANG RETURNS,", "SHARES SURGE"],
          "Nvidia reinstates Jensen Huang as chief. Stocks rebound after a sell-off.",
          lambda ax, ay, aw, ah: draw_chart(cv, ax - 6, ay + 52, 128, 92))
    panel(cv, gx, gy + ph + gap, pw, ph, "SPORT * GENEVA",
          ["CHESS CROWN", "BATTLE BEGINS"],
          "Gukesh defends his title against Sindarov. Game 1 today.",
          lambda ax, ay, aw, ah: draw_chess(cv, ax + 14, ay + 48, 80))
    panel(cv, gx + pw + gap, gy + ph + gap, pw, ph, "DISASTER * INDONESIA",
          ["24 DEAD IN", "FACTORY FIRE"],
          "Rescuers search for about 30 missing after a blaze at a candy factory.",
          lambda ax, ay, aw, ah: draw_factory(cv, ax - 2, ay + 52, 118, 88))
    panel(cv, gx, gy + 2 * (ph + gap), pw, ph, "MEDIA * NEW YORK",
          ["REUTERS STAFF", "VOTE TO STRIKE"],
          "94% back strike action in a dispute over AI protections, the union says.",
          lambda ax, ay, aw, ah: draw_text(cv, ax + 8, ay + 78, "94%", 5, RED))

    # locator panel: where the news happened (no new story)
    mx, my = gx + pw + gap, gy + 2 * (ph + gap)
    cv.rect(mx, my, pw, ph, SKY)
    cv.frame(mx, my, pw, ph, INK, 2)
    draw_text(cv, mx + 16, my + 14, "WHERE THE NEWS HAPPENED", 2, RED)
    cv.hline(mx + 16, my + 34, pw - 32, LIGHT, 2)
    for label, dx, dy in (("ANTALYA", 252, 66), ("BENGHAZI", 232, 96),
                          ("GENEVA", 200, 40), ("NEW YORK", 52, 48),
                          ("INDONESIA", 348, 126)):
        cv.disc(mx + dx, my + dy, 7, RED)
        cv.ring(mx + dx, my + dy, 7, WHITE, 2)
        draw_text(cv, mx + dx + 12, my + dy - 7, label, 2, INK)
    cv.rect(0, H - 10, W, 10, INK)
    return cv


def encode_png(cv):
    raw = bytearray()
    row = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * row:(y + 1) * row])

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(build())
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, 0o644)


if __name__ == "__main__":
    main()
