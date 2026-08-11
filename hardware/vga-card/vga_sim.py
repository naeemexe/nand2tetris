#!/usr/bin/env python3
"""
Clock-by-clock simulation of the VGA card, using the decoders that
vga_timing.design() picked (not the ideal formulas), so a bad gate
choice shows up here before it's wired.

    python3 vga_sim.py               measure the signals, render build/frame.png

Model of one 10 MHz clock edge (everything synchronous):
  - H counter: next = 0 if hclear decoded, else +1           (74LS163 x3)
  - V counter: counts only when hclear (lineEnd); clears on vclear
  - each J-K flip-flop looks at its J/K decoders BEFORE the edge  (74LS109)
  - pixel latch (74HCT374) grabs the EEPROM output when the H count goes
    from odd to even, i.e. at the end of each 2-clock image pixel. The
    address has then been steady for 200 ns, longer than the EEPROM's
    150 ns access time.
  - colour output = latch if hdisplay AND vdisplay, else 0 V (the latch's
    /OE turns its outputs off and the monitor's 75 ohm pulls them low)
"""
from pathlib import Path

from vga_timing import (H_TOTAL, V_TOTAL, CLOCK_HZ, H_EVENTS, V_EVENTS, design)
from png import write_png

HERE = Path(__file__).parent


class VgaCard:
    def __init__(self, rom: bytes):
        self.rom = rom
        self.dec = design()
        self.h = self.v = 0
        self.ff = {name: 0 for name in list(H_EVENTS) + list(V_EVENTS)}
        self.latch = 0

    def address(self):
        return ((self.v >> 3) & 0x7F) << 7 | ((self.h >> 1) & 0x7F)

    def outputs(self):
        visible = self.ff["hdisplay"] and self.ff["vdisplay"]
        return self.ff["hsync"], self.ff["vsync"], (self.latch if visible else 0)

    def edge(self):
        d = self.dec
        line_end = d["hclear"].fires(self.h)
        # every flip-flop samples its inputs as they are right now...
        new = {}
        for name, q in self.ff.items():
            count, gate = (self.h, True) if name in H_EVENTS else (self.v, line_end)
            j = gate and d[name + ".J"].fires(count)
            k = gate and d[name + ".K"].fires(count)
            new[name] = (q ^ 1) if (j and k) else 1 if j else 0 if k else q
        if self.h & 1:                                  # odd -> even: end of an image pixel
            self.latch = self.rom[self.address()] & 0x3F
        # ...and then everything changes together
        self.ff = new
        if line_end:
            self.v = 0 if d["vclear"].fires(self.v) else self.v + 1
        self.h = 0 if line_end else self.h + 1

    def frame(self):
        """Run one frame from (h, v) = (0, 0); returns samples[v][h] = (hsync, vsync, rgb)."""
        out = []
        for _ in range(V_TOTAL):
            line = []
            for _ in range(H_TOTAL):
                line.append(self.outputs())
                self.edge()
            out.append(line)
        return out


def runs(signal):
    """[(start, length)] of the 1-runs in a list of 0/1."""
    result, start = [], None
    for i, s in enumerate(signal + [0]):
        if s and start is None:
            start = i
        elif not s and start is not None:
            result.append((start, i - start))
            start = None
    return result


def measure(samples):
    hsync_line = [s[0] for s in samples[0]]
    vsync_col = [line[0][1] for line in samples]
    visible_rows = [v for v, line in enumerate(samples) if any(s[2] for s in line)]
    visible_cols = sorted({h for line in samples for h, s in enumerate(line) if s[2]})
    return {
        "hsync runs (clock)": runs(hsync_line),
        "vsync runs (line)": runs(vsync_col),
        "line rate kHz": CLOCK_HZ / H_TOTAL / 1e3,
        "frame rate Hz": CLOCK_HZ / H_TOTAL / V_TOTAL,
        "lit rows": (visible_rows[0], visible_rows[-1]) if visible_rows else None,
        "lit cols": (visible_cols[0], visible_cols[-1]) if visible_cols else None,
    }


def render(samples, path):
    """What the monitor shows: the 200 x 600 visible samples, each 4 pixels wide."""
    hon, hoff = H_EVENTS["hdisplay"]
    rows = []
    for v in range(600):
        row = []
        for h in range(hon, hoff):
            c = samples[v][h][2]
            row.extend([((c >> 4 & 3) * 85, (c >> 2 & 3) * 85, (c & 3) * 85)] * 4)
        rows.append(row)
    write_png(path, 800, 600, rows)


def main():
    rom_path = HERE / "build" / "image.bin"
    if not rom_path.exists():
        raise SystemExit("run image_to_rom.py first")
    card = VgaCard(rom_path.read_bytes())
    card.frame()                                       # first frame: flip-flops settle
    samples = card.frame()
    for k, v in measure(samples).items():
        print(f"{k:20} {v}")
    render(samples, HERE / "build" / "frame.png")
    print("wrote build/frame.png")


if __name__ == "__main__":
    main()
