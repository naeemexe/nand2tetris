"""
VGA card checks.  Run:  python3 tests/test_vga.py   (or python3 -m pytest tests)
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import vga_timing as T                                   # noqa: E402
from image_to_rom import test_pattern as make_pattern, to_rom, crop_43, downscale   # noqa: E402
from png import read_png, write_png                      # noqa: E402
from vga_sim import VgaCard, measure                     # noqa: E402

ROM = to_rom(make_pattern())
_card = VgaCard(ROM)
_card.frame()                                            # let the flip-flops settle
FRAME = _card.frame()


def test_numbers_match_vesa():
    assert T.H_TOTAL * 4 == 1056 and T.V_TOTAL == 628
    assert abs(T.CLOCK_HZ / T.H_TOTAL - 37_879) < 1      # line rate, Hz
    assert abs(T.CLOCK_HZ / T.H_TOTAL / T.V_TOTAL - 60.317) < 0.01


def test_sync_pulses():
    m = measure(FRAME)
    assert m["hsync runs (clock)"] == [(210, 32)]       # 3.2 us, after a 1 us front porch
    assert m["vsync runs (line)"] == [(601, 4)]
    for line in FRAME:                                   # hsync identical on every line
        assert [s[0] for s in line] == [s[0] for s in FRAME[0]]


def test_picture_is_exactly_the_rom():
    hon, hoff = T.H_EVENTS["hdisplay"]
    for v, line in enumerate(FRAME):
        for h, (_, _, rgb) in enumerate(line):
            if v < 600 and hon <= h < hoff:
                x, y = (h - hon) // 2, v // 8
                assert rgb == ROM[y * 128 + x], (h, v)
            else:
                assert rgb == 0, f"not blanked at h={h} v={v}"


def test_naive_decoding_breaks_hsync():
    """The tempting shortcut - AND only the 1-bits of each count - makes hsync's
    set (209) also fire at 241, the same clock as its reset: J=K=1 toggles."""
    on, off = T.H_EVENTS["hsync"]
    j = T.Decoder(on - 1, on - 1, 0)
    k = T.Decoder(off - 1, off - 1, 0)
    assert j.fires(241) and k.fires(241)
    assert T.simulate_jk(j, k, T.H_TOTAL) != T.ideal_wave(on, off, T.H_TOTAL)


def test_designed_decoders_are_exact():
    d = T.design()
    for name, (on, off) in T.H_EVENTS.items():
        assert T.simulate_jk(d[name + ".J"], d[name + ".K"], T.H_TOTAL) == T.ideal_wave(on, off, T.H_TOTAL)
    for name, (on, off) in T.V_EVENTS.items():
        assert T.simulate_jk(d[name + ".J"], d[name + ".K"], T.V_TOTAL) == T.ideal_wave(on, off, T.V_TOTAL)
    assert [c for c in range(T.H_TOTAL) if d["hclear"].fires(c)] == [T.H_TOTAL - 1]
    assert [c for c in range(T.V_TOTAL) if d["vclear"].fires(c)] == [T.V_TOTAL - 1]


def test_dac_levels_are_even_and_in_range():
    levels = [T.dac_level(m, l, 620, 1200, 4.5) for m, l in ((0, 0), (0, 1), (1, 0), (1, 1))]
    assert levels[0] == 0 and abs(levels[3] - 0.7) < 0.02
    steps = [b - a for a, b in zip(levels, levels[1:])]
    assert max(steps) - min(steps) < 0.03                # roughly linear


def test_png_roundtrip_and_conversion():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wide.png"
        # 400x200 (2:1) image: left half red, right half blue
        rows = [[(255, 0, 0) if x < 200 else (0, 0, 255) for x in range(400)] for _ in range(200)]
        write_png(path, 400, 200, rows)
        w, h, back = read_png(path)
        assert (w, h) == (400, 200) and back == rows
        w, h, cropped = crop_43(w, h, back)
        assert (w, h) == (266, 200)                      # sides trimmed to 4:3
        small = downscale(w, h, cropped, 100, 75)
        rom = to_rom(small)
        assert rom[0] == 0b110000 and rom[99] == 0b000011   # red left, blue right


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
