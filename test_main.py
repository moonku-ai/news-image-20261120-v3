"""Tests for news-image-20261120 v3 (pure stdlib PNG news poster).

Run: python3 -m unittest test_main -v  (from the repo dir)
TDD: these tests were written BEFORE main.py existed.
"""
import binascii
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

W = H = 1024
MAX_BYTES = 1048576


def decode_png(path):
    """Minimal PNG decoder: returns (width, height, rows) with rows as bytes of RGB."""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    width = height = None
    bit_depth = color_type = None
    idat = b""
    saw_iend = False
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        crc_stored, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        crc_calc = binascii.crc32(ctype)
        crc_calc = binascii.crc32(chunk, crc_calc) & 0xFFFFFFFF
        assert crc_calc == crc_stored, "bad CRC in %s chunk" % ctype.decode("latin1")
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            saw_iend = True
        pos += 12 + length
    assert saw_iend, "missing IEND"
    assert bit_depth == 8 and color_type == 2, "expect 8-bit RGB"
    raw = zlib.decompress(idat)
    stride = width * 3
    rows = []
    p = 0
    for _ in range(height):
        assert raw[p] == 0, "expect filter 0 scanlines"
        rows.append(raw[p + 1:p + 1 + stride])
        p += 1 + stride
    assert p == len(raw), "trailing data after last scanline"
    return width, height, rows


def pixel(rows, x, y):
    row = rows[y]
    return tuple(row[x * 3:x * 3 + 3])


def region_has_color(rows, x0, y0, x1, y1, color, min_count=20):
    count = 0
    for y in range(y0, y1, 2):
        row = rows[y]
        for x in range(x0, x1, 2):
            if tuple(row[x * 3:x * 3 + 3]) == color:
                count += 1
                if count >= min_count:
                    return True
    return False


class TestEntryImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import main
        cls.main = main
        cls.tmp = tempfile.mkdtemp(prefix="newsimg-v3-test-")
        cls.out1 = os.path.join(cls.tmp, "run1")
        cls.out2 = os.path.join(cls.tmp, "run2")
        os.makedirs(cls.out1)
        os.makedirs(cls.out2)
        main.main(cls.out1)
        main.main(cls.out2)
        cls.png1 = os.path.join(cls.out1, "entry.png")
        cls.png2 = os.path.join(cls.out2, "entry.png")
        cls.w, cls.h, cls.rows = decode_png(cls.png1)

    def test_png_structure_valid(self):
        # decode_png already asserts signature, per-chunk CRCs and IEND.
        self.assertEqual((self.w, self.h), (1024, 1024))

    def test_dimensions_1024x1024(self):
        self.assertEqual(self.w, 1024)
        self.assertEqual(self.h, 1024)

    def test_size_under_1mib(self):
        size = os.path.getsize(self.png1)
        self.assertLessEqual(size, MAX_BYTES, "entry.png %d bytes > 1 MiB" % size)

    def test_deterministic_two_runs_byte_identical(self):
        b1 = open(self.png1, "rb").read()
        b2 = open(self.png2, "rb").read()
        self.assertEqual(b1, b2, "two runs must write identical bytes")

    def test_main_writes_entry_png(self):
        self.assertTrue(os.path.isfile(self.png1))
        self.assertGreater(os.path.getsize(self.png1), 10000)

    def test_date_line_constant(self):
        self.assertEqual(self.main.DATE_LINE, "FRIDAY 20 NOVEMBER 2026")

    def test_font_covers_every_character_used(self):
        used = set()
        for s in self.main.ALL_STRINGS:
            used.update(s)
        missing = sorted(c for c in used if c not in self.main.FONT)
        self.assertEqual(missing, [], "font missing glyphs: %r" % missing)
        # every used char must actually draw non-blank pixels (except space)
        for c in sorted(used):
            if c == " ":
                continue
            img = self.main.new_image(60, 20)
            self.main.draw_text(img, c, 2, 2, 3, self.main.INK)
            self.assertTrue(any(b != 0 for b in img.buf),
                            "glyph %r draws nothing" % c)

    def test_wrap_fits_frame_width(self):
        for frame in self.main.FRAMES:
            for text, scale in ((frame["headline"], 3),
                                (frame["body"], 2)):
                lines = self.main.wrap_text(text, self.main.FRAME_TEXT_W, scale)
                self.assertLessEqual(len(lines), 3,
                                     "too many lines for %r" % text)
                for line in lines:
                    self.assertLessEqual(
                        self.main.text_width(line, scale),
                        self.main.FRAME_TEXT_W,
                        "line %r overflows frame" % line)

    def test_masthead_has_cream_text(self):
        # masthead band y 16..128 must contain cream pixels (the date text)
        self.assertTrue(region_has_color(self.rows, 16, 16, 1008, 128,
                                         self.main.CREAM, min_count=200))

    def test_each_frame_has_its_accent(self):
        for frame in self.main.FRAMES:
            x0, y0, x1, y1 = frame["box"]
            self.assertTrue(
                region_has_color(self.rows, x0, y0, x1, y1,
                                 frame["accent"], min_count=100),
                "frame %r lacks its accent colour" % frame["kicker"])

    def test_ticker_has_cream_text(self):
        self.assertTrue(region_has_color(self.rows, 16, 884, 1008, 960,
                                         self.main.CREAM, min_count=100))

    def test_paper_background_present(self):
        # corners of the page are the paper colour
        self.assertEqual(pixel(self.rows, 4, 4), self.main.PAPER)
        self.assertEqual(pixel(self.rows, 1019, 1019), self.main.PAPER)

    def test_output_dir_env_respected(self):
        tmp = tempfile.mkdtemp(prefix="newsimg-v3-env-")
        env = dict(os.environ, MAKEFUN_OUTPUT_DIR=tmp)
        code = ("import sys; sys.path.insert(0, %r); import main; main.main()"
                % os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run([sys.executable, "-c", code], env=env,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertTrue(os.path.isfile(os.path.join(tmp, "entry.png")))


if __name__ == "__main__":
    unittest.main()
