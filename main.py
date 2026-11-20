"""news-image-20261120 v3 — "FOUR FRAMES".

Pure Python stdlib program. Draws a 1024x1024 poster-style front page that
sums up Friday 20 November 2026 world news in four large pictogram frames
plus an "also today" ticker, and writes it to /output/entry.png.

Design: warm paper, black masthead band, 2x2 frames with thick ink borders
and flat-colour pictograms (cyclone spiral, scales of justice, rising chart,
missile) — each story readable from its picture + short labels at 300px.
"""
import math
import os
import struct
import zlib

W = H = 1024

# --- palette ---
PAPER = (250, 246, 236)
INK = (20, 20, 20)
CREAM = (250, 246, 236)
GOLD = (232, 163, 23)
WHITE = (255, 255, 255)
VERMILION = (199, 62, 29)   # frame 1 accent: cyclone
TEAL = (14, 107, 98)        # frame 2 accent: justice
AMBER = (185, 127, 14)      # frame 3 accent: markets
STEEL = (51, 88, 122)       # frame 4 accent: war

DATE_LINE = "FRIDAY 20 NOVEMBER 2026"
SUB_LINE = "THE WORLD IN FOUR FRAMES"

FRAMES = [
    {
        "box": (16, 140, 508, 500),
        "accent": VERMILION,
        "kicker": "1 - CYCLONE - TODAY 20 NOV",
        "headline": "CYCLONE AKVAN HITS ODISHA",
        "body": ("300,000+ EVACUATED AS THE STORM LANDS AT NOON; "
                 "WINDS 110 KM/H; 423 RESCUE TEAMS OUT."),
        "dateline": "GOPALPUR, ODISHA",
        "pic": "cyclone",
    },
    {
        "box": (516, 140, 1008, 500),
        "accent": TEAL,
        "kicker": "2 - JUSTICE - VERDICT 19 NOV",
        "headline": "MYANMAR GUILTY OF GENOCIDE",
        "body": ("ICJ RULES 9-6: FIRST STATE EVER FOUND GUILTY OF "
                 "GENOCIDE. UK EXPELS MYANMAR ATTACHE."),
        "dateline": "THE HAGUE",
        "pic": "scales",
    },
    {
        "box": (16, 512, 508, 872),
        "accent": AMBER,
        "kicker": "3 - MARKETS - TODAY 20 NOV",
        "headline": "ANTHROPIC GOES PUBLIC",
        "body": ("FIRST PURELY AI COMPANY LISTED AS ITS SHARES DEBUT; "
                 "AMONG THE WORLD'S MOST VALUABLE."),
        "dateline": "WORLD MARKETS",
        "pic": "chart",
    },
    {
        "box": (516, 512, 1008, 872),
        "accent": STEEL,
        "kicker": "4 - WAR - TODAY 20 NOV",
        "headline": "KYIV HIT BY MISSILES",
        "body": ("FOUR BALLISTIC MISSILES STRIKE THE CAPITAL OVERNIGHT; "
                 "EUROPE READIES RUSSIA TALKS."),
        "dateline": "KYIV, UKRAINE",
        "pic": "missile",
    },
]

TICKER = [
    "ALSO TODAY: TANKER HITS MINE OFF HORMUZ - GENOA AIRPORT SHUT BY DRONES",
    "HOUTHIS HIT SAUDI TARGETS - SEOUL ORDERS HAN RETRIAL - PEACE DECLARATION",
    "CALIFORNIA PROBES NVIDIA - TRUMP PARDONS PETE ROSE - SENSEX +1.2%",
]
FOOTER = "FRIDAY 20 NOVEMBER 2026 - SOURCES: IMD, REUTERS, BBC, AP"

FRAME_TEXT_W = 464

ALL_STRINGS = (
    [DATE_LINE, SUB_LINE, FOOTER] + TICKER
    + [v for f in FRAMES for v in
        (f["kicker"], f["headline"], f["body"], f["dateline"])]
)

# --- 5x7 bitmap font (own hand-drawn glyphs, 7 rows of 5 bits) ---
_G = {
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}
FONT = _G


class Img:
    def __init__(self, w, h, color=(0, 0, 0)):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(color) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)


def new_image(w, h, color=(0, 0, 0)):
    return Img(w, h, color)


def fill_rect(img, x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(img.w, x1)
    y1 = min(img.h, y1)
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * img.w + x0) * 3
        img.buf[i:i + len(row)] = row


def draw_rect(img, x0, y0, x1, y1, color, t=1):
    for k in range(t):
        for x in range(x0 + k, x1 - k):
            img.set(x, y0 + k, color)
            img.set(x, y1 - 1 - k, color)
        for y in range(y0 + k, y1 - k):
            img.set(x0 + k, y, color)
            img.set(x1 - 1 - k, y, color)


def line(img, x0, y0, x1, y1, color, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for a in range(-(t // 2), t // 2 + 1):
            for b in range(-(t // 2), t // 2 + 1):
                img.set(x + a, y + b, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def fill_circle(img, cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        half = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
        for x in range(cx - half, cx + half + 1):
            img.set(x, y, color)


def fill_ellipse(img, cx, cy, rx, ry, color):
    for y in range(cy - ry, cy + ry + 1):
        v = 1.0 - ((y - cy) / ry) ** 2
        half = int(rx * math.sqrt(max(0.0, v)))
        for x in range(cx - half, cx + half + 1):
            img.set(x, y, color)


def fill_poly(img, pts, color):
    pts = [(int(round(x)), int(round(y))) for x, y in pts]
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(int(math.ceil(xs[k])), int(xs[k + 1]) + 1):
                img.set(x, y, color)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(img, text, x, y, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "1":
                    fill_rect(img, cx + c * scale, y + r * scale,
                              cx + (c + 1) * scale, y + (r + 1) * scale,
                              color)
        cx += 6 * scale


def draw_text_centered(img, text, cx, y, scale, color):
    draw_text(img, text, cx - text_width(text, scale) // 2, y, scale, color)


def wrap_text(text, max_w, scale):
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- pictograms (drawn in the frame's picture area, centred on cx, cy) ---

def pic_cyclone(img, cx, cy, accent):
    # spiral storm: archimedean spiral of dots + arms
    for deg in range(0, 700, 4):
        t = math.radians(deg)
        r = 5 + deg * 0.085
        x = int(cx + r * math.cos(t))
        y = int(cy + r * math.sin(t) * 0.92)
        fill_circle(img, x, y, 4, accent)
    # eye
    fill_circle(img, cx, cy, 9, PAPER)
    draw_rect(img, cx - 9, cy - 9, cx + 10, cy + 10, accent, 2)
    # coastline along the bottom
    coast = [(cx - 150, cy + 78), (cx - 90, cy + 62), (cx - 30, cy + 74),
             (cx + 30, cy + 60), (cx + 90, cy + 72), (cx + 150, cy + 64)]
    for a, b in zip(coast, coast[1:]):
        line(img, a[0], a[1], b[0], b[1], INK, 3)
    # rain slashes, upper right
    for i in range(6):
        x = cx + 95 + i * 9
        y = cy - 62 + (i % 2) * 14
        line(img, x, y, x - 6, y + 14, STEEL, 2)


def pic_scales(img, cx, cy, accent):
    # post, beam, two pans, base
    fill_rect(img, cx - 4, cy - 58, cx + 5, cy + 52, accent)
    fill_circle(img, cx, cy - 62, 7, accent)
    fill_rect(img, cx - 78, cy - 58, cx + 79, cy - 50, accent)
    for sx in (-78, 78):
        line(img, cx + sx, cy - 50, cx + sx - 26, cy + 2, INK, 2)
        line(img, cx + sx, cy - 50, cx + sx + 26, cy + 2, INK, 2)
        line(img, cx + sx - 26, cy + 2, cx + sx + 26, cy + 2, INK, 2)
        fill_ellipse(img, cx + sx, cy + 8, 27, 9, INK)
    fill_rect(img, cx - 42, cy + 52, cx + 43, cy + 60, accent)
    # big 9-6 verdict numerals under the beam
    draw_text_centered(img, "9-6", cx, cy - 34, 4, INK)


def pic_chart(img, cx, cy, accent):
    base = cy + 48
    heights = (34, 52, 70, 92)
    xs = [cx - 84, cx - 42, cx, cx + 42]
    for x, hh in zip(xs, heights):
        fill_rect(img, x, base - hh, x + 30, base, accent)
    fill_rect(img, cx - 100, base, cx + 100, base + 5, INK)
    # rising arrow over the bars
    line(img, cx - 96, base - 30, cx + 88, base - 108, INK, 4)
    line(img, cx + 88, base - 108, cx + 58, base - 106, INK, 4)
    line(img, cx + 88, base - 108, cx + 86, base - 78, INK, 4)
    # AI label clear of the arrow, top-left of the picture area
    draw_text(img, "AI", cx - 150, cy - 74, 3, INK)


def pic_missile(img, cx, cy, accent):
    # buildings along the bottom
    for bx, bw, bh in ((cx - 150, 52, 46), (cx - 88, 40, 66),
                       (cx - 38, 46, 38), (cx + 18, 38, 58),
                       (cx + 66, 48, 42), (cx + 122, 30, 52)):
        fill_rect(img, bx, cy + 78 - bh, bx + bw, cy + 78, INK)
    # missile body, nose up-right — wide enough to read as a missile
    d = (0.7071, -0.7071)
    p = (0.7071, 0.7071)
    nose = (cx + 62, cy - 62)
    tail = (cx - 38, cy + 38)
    pts = [
        nose,
        (tail[0] + p[0] * 14, tail[1] + p[1] * 14),
        (tail[0] - p[0] * 14, tail[1] - p[1] * 14),
    ]
    fill_poly(img, pts, accent)
    # fins
    fill_poly(img, [(tail[0], tail[1]),
                    (tail[0] - 26, tail[1] + 4),
                    (tail[0] - 4, tail[1] + 26)], accent)
    # exhaust burst
    bx, by = tail[0] - 14, tail[1] + 14
    for ang in range(0, 360, 30):
        t = math.radians(ang)
        line(img, bx, by, int(bx + 26 * math.cos(t)),
             int(by + 26 * math.sin(t)), VERMILION, 3)
    fill_circle(img, bx, by, 8, GOLD)


PICS = {
    "cyclone": pic_cyclone,
    "scales": pic_scales,
    "chart": pic_chart,
    "missile": pic_missile,
}


def draw_frame(img, frame):
    x0, y0, x1, y1 = frame["box"]
    accent = frame["accent"]
    fill_rect(img, x0, y0, x1, y1, PAPER)
    draw_rect(img, x0, y0, x1, y1, INK, 4)
    # kicker strip
    fill_rect(img, x0 + 4, y0 + 4, x1 - 4, y0 + 44, accent)
    draw_text(img, frame["kicker"], x0 + 16, y0 + 15, 2, WHITE)
    # pictogram area
    cx = (x0 + x1) // 2
    cy = y0 + 122
    PICS[frame["pic"]](img, cx, cy, accent)
    # headline
    lines = wrap_text(frame["headline"], FRAME_TEXT_W, 3)
    y = y0 + 206
    for ln in lines:
        draw_text(img, ln, x0 + 14, y, 3, INK)
        y += 26
    # body
    y = y0 + 258
    for ln in wrap_text(frame["body"], FRAME_TEXT_W, 2):
        draw_text(img, ln, x0 + 14, y, 2, INK)
        y += 18
    # dateline strip at the bottom
    line(img, x0 + 14, y1 - 42, x1 - 14, y1 - 42, accent, 2)
    draw_text(img, frame["dateline"], x0 + 14, y1 - 34, 2, accent)


def draw(img):
    fill_rect(img, 0, 0, W, H, PAPER)
    # masthead
    fill_rect(img, 16, 16, 1008, 128, INK)
    draw_text_centered(img, DATE_LINE, W // 2, 30, 6, CREAM)
    draw_text_centered(img, SUB_LINE, W // 2, 90, 2, GOLD)
    # frames
    for frame in FRAMES:
        draw_frame(img, frame)
    # ticker
    fill_rect(img, 16, 884, 1008, 968, INK)
    y = 896
    for ln in TICKER:
        draw_text_centered(img, ln, W // 2, y, 2, CREAM)
        y += 22
    # footer
    draw_text_centered(img, FOOTER, W // 2, 980, 2, INK)


def encode_png(img):
    raw = bytearray()
    stride = img.w * 3
    for y in range(img.h):
        raw.append(0)
        raw += img.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        out += struct.pack(">I", binascii_crc(ctype + data))
        return out

    ihdr = struct.pack(">IIBBBBB", img.w, img.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def binascii_crc(data):
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF


def main(outdir=None):
    outdir = outdir or os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    img = new_image(W, H, PAPER)
    draw(img)
    data = encode_png(img)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))
    return path


if __name__ == "__main__":
    main()
