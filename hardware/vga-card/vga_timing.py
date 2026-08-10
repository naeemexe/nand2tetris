#!/usr/bin/env python3
"""
Timing design for the discrete-logic VGA card.

    python3 vga_timing.py      prints the whole derivation + the gate wiring table

Start from the VESA standard for 800x600 @ 60 Hz:

                     visible  front porch  sync  back porch  total   sync polarity
    horizontal (px)    800        40        128      88      1056       +
    vertical (lines)   600         1          4      23       628       +
    pixel clock 40 MHz

A 40 MHz clock is too fast for 74LS logic, but a monitor doesn't care how
many pixels you send per line - only that the SYNC timing is right. So run
at 10 MHz = 40 / 4 and divide every horizontal number by 4. The line rate
(and therefore everything vertical) is unchanged:

    horizontal (10 MHz clocks): 200 visible, 10 front porch, 32 sync, 22 back porch = 264
    line rate  = 10 MHz / 264 = 37.879 kHz   (VESA: 37.879 kHz)
    frame rate = 37.879 kHz / 628 = 60.32 Hz

Image: 100 x 75 pixels. Each image pixel = 2 clocks wide (8 real pixels)
and 8 lines tall (8 real pixels) - square pixels again.
    x = hcount bits 7..1   (0..99 while visible)
    y = vcount bits 9..3   (0..74 while visible)
    EEPROM address = y * 128 + x  ->  A6..A0 = x, A13..A7 = y
"""

# ---- spec ----------------------------------------------------------------
CLOCK_HZ = 10_000_000
H_VISIBLE, H_FRONT, H_SYNC, H_BACK = 200, 10, 32, 22
V_VISIBLE, V_FRONT, V_SYNC, V_BACK = 600, 1, 4, 23
H_TOTAL = H_VISIBLE + H_FRONT + H_SYNC + H_BACK      # 264
V_TOTAL = V_VISIBLE + V_FRONT + V_SYNC + V_BACK      # 628
H_BITS, V_BITS = 9, 10                               # 264 needs 9 bits, 628 needs 10
IMAGE_W, IMAGE_H = 100, 75

# The pixel latch (74HCT374) delays the picture by one image pixel = 2 clocks,
# so the horizontal display window is shifted by the same 2 clocks.
PIXEL_DELAY = 2

# ---- events -----------------------------------------------------------------
# Every output is a J-K flip-flop clocked by the 10 MHz clock. A flip-flop
# changes on the clock edge AFTER its J/K input is seen, so to switch at count
# N we decode N-1. (Same trick for the synchronous counter clear: decode the
# last count, the counter goes to 0 on the next edge.)
#
#            name       on at                            off at
H_EVENTS = {"hdisplay": (PIXEL_DELAY, H_VISIBLE + PIXEL_DELAY),
            "hsync":    (H_VISIBLE + H_FRONT, H_VISIBLE + H_FRONT + H_SYNC)}
V_EVENTS = {"vdisplay": (0, V_VISIBLE),
            "vsync":    (V_VISIBLE + V_FRONT, V_VISIBLE + V_FRONT + V_SYNC)}


def ideal_wave(on: int, off: int, total: int) -> list[int]:
    return [1 if on <= c < off else 0 for c in range(total)]


# ---- decoder design ---------------------------------------------------------
# A decoder is an AND gate fed by some counter bits (true) and some inverted
# bits. Decoding ALL bits is always correct but costs inputs and inverters.
# Because the counter only ever goes 0..total-1, and because a J-K flip-flop
# ignores "set" when it's already set, we can often drop bits. This finds the
# smallest decoders and checks the result by simulating a whole cycle.

class Decoder:
    def __init__(self, value: int, ones: int, zeros: int):
        self.value, self.ones, self.zeros = value, ones, zeros

    def fires(self, count: int) -> bool:
        return (count & self.ones) == self.ones and (count & self.zeros) == 0

    def inputs(self, bits: int) -> str:
        names = [f"Q{b}" for b in range(bits - 1, -1, -1) if self.ones >> b & 1]
        names += [f"/Q{b}" for b in range(bits - 1, -1, -1) if self.zeros >> b & 1]
        return " & ".join(names)


def simulate_jk(j: Decoder, k: Decoder, total: int, start: int = 0) -> list[int]:
    """Output of a J-K flip-flop over one counter cycle (run twice to settle)."""
    q = start
    wave = [0] * total
    for _ in range(2):
        for c in range(total):
            wave[c] = q
            jf, kf = j.fires(c), k.fires(c)
            if jf and kf:
                q ^= 1          # J=K=1 toggles - almost always a bug
            elif jf:
                q = 1
            elif kf:
                q = 0
    return wave


def minimal_decoders(on: int, off: int, total: int, bits: int):
    """Smallest J and K decoders whose flip-flop output equals the ideal wave."""
    target = ideal_wave(on, off, total)
    j_val, k_val = (on - 1) % total, (off - 1) % total
    full = (1 << bits) - 1
    j = Decoder(j_val, j_val, full & ~j_val)          # start fully decoded: surely right
    k = Decoder(k_val, k_val, full & ~k_val)
    assert simulate_jk(j, k, total) == target

    # Greedily remove inputs (inverted ones first - they need inverter chips)
    # as long as the waveform stays exactly right.
    changed = True
    while changed:
        changed = False
        for dec in (j, k):
            for attr in ("zeros", "ones"):
                for b in range(bits):
                    mask = getattr(dec, attr)
                    if not mask >> b & 1:
                        continue
                    setattr(dec, attr, mask & ~(1 << b))
                    if simulate_jk(j, k, total) == target:
                        changed = True
                    else:
                        setattr(dec, attr, mask)
    return j, k


def minimal_clear(last: int, total: int, bits: int) -> Decoder:
    """Counter-clear decoder: must fire at 'last' and NOWHERE else in 0..total-1."""
    full = (1 << bits) - 1
    dec = Decoder(last, last, full & ~last)
    for attr in ("zeros", "ones"):
        for b in range(bits):
            mask = getattr(dec, attr)
            if not mask >> b & 1:
                continue
            setattr(dec, attr, mask & ~(1 << b))
            if [c for c in range(total) if dec.fires(c)] != [last]:
                setattr(dec, attr, mask)
    return dec


def design():
    """All decoders of the card: {name: Decoder}."""
    d = {"hclear": minimal_clear(H_TOTAL - 1, H_TOTAL, H_BITS),
         "vclear": minimal_clear(V_TOTAL - 1, V_TOTAL, V_BITS)}
    for name, (on, off) in H_EVENTS.items():
        d[name + ".J"], d[name + ".K"] = minimal_decoders(on, off, H_TOTAL, H_BITS)
    for name, (on, off) in V_EVENTS.items():
        d[name + ".J"], d[name + ".K"] = minimal_decoders(on, off, V_TOTAL, V_BITS)
    return d


# ---- DAC ----------------------------------------------------------------------
# Each colour channel has 2 bits -> 4 levels. The monitor input is 75 ohm to
# ground and wants 0..0.7 V. Two resistors, the MSB's half the LSB's, form a
# binary-weighted DAC with that 75 ohm. A low output pulls its resistor to 0 V.

def dac_level(msb: int, lsb: int, r_msb: float, r_lsb: float, v_high: float, load=75.0) -> float:
    """Exact node voltage (Millman's theorem): sum(V/R) / sum(1/R)."""
    num = (v_high if msb else 0) / r_msb + (v_high if lsb else 0) / r_lsb
    den = 1 / r_msb + 1 / r_lsb + 1 / load
    return num / den


def dac_resistor(v_high: float, full_scale=0.7, load=75.0) -> float:
    """R_msb such that both bits high give full_scale, with R_lsb = 2 * R_msb.
    Both high: the two resistors are in parallel = 2R/3, a divider with 75 ohm."""
    r_parallel = load * (v_high / full_scale - 1)
    return r_parallel * 3 / 2


def report():
    print(__doc__)
    line_hz = CLOCK_HZ / H_TOTAL
    print(f"line rate  {line_hz / 1e3:.3f} kHz, frame rate {line_hz / V_TOTAL:.2f} Hz")
    print(f"hsync pulse {H_SYNC / CLOCK_HZ * 1e6:.2f} us (VESA 3.2 us), "
          f"vsync pulse {V_SYNC} lines = {V_SYNC / line_hz * 1e6:.1f} us\n")

    print("Gate wiring (AND these counter outputs; /Qn = through an inverter):")
    for name, dec in design().items():
        bits = V_BITS if name[0] == "v" else H_BITS
        what = "clear counter" if name.endswith("clear") else ("set (J)" if name.endswith("J") else "reset (K)")
        extra = "  & lineEnd" if name[0] == "v" else ""
        print(f"  {name:<11} {what:<14} at count {dec.value:3}:  {dec.inputs(bits)}{extra}")

    print("\nDAC, assuming the 74HCT374 outputs swing to ~4.5 V under load:")
    r = dac_resistor(4.5)
    print(f"  ideal R_msb = {r:.0f} ohm, R_lsb = {2 * r:.0f} ohm  ->  use 620 and 1.2k (E24)")
    for msb, lsb in ((0, 0), (0, 1), (1, 0), (1, 1)):
        print(f"  bits {msb}{lsb}: {dac_level(msb, lsb, 620, 1200, 4.5):.3f} V")


if __name__ == "__main__":
    report()
