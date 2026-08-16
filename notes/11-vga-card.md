# 11 — The VGA video card

**Goal:** make a monitor display a picture using only counters, gates, flip-flops,
an EEPROM and resistors. No microcontroller, no video chip.
Idea from Ben Eater's video card (eater.net/vga); the numbers, decoder design and
pixel pipeline below are derived from the VESA spec and verified by simulation
in `hardware/vga-card/`.

---

## 1. How VGA works

VGA is analog and very simple. Five signals matter:

| pin | signal | meaning |
|---|---|---|
| 1, 2, 3 | R, G, B | brightness of the current pixel, 0 – 0.7 V |
| 13 | HSYNC | "start a new line" pulse |
| 14 | VSYNC | "start a new frame" pulse |

The monitor scans left → right, top → bottom. **It has no idea where pixels are.**
It only locks onto the timing of the sync pulses and samples the colour
voltage continuously. Everything we build is timing.

Each line (and each frame) has four parts:

```
|<------- visible ------->|<-front->|<--sync-->|<-back->|
 colour data                 black      pulse     black
                             porch               porch
```
The porches are blank margins, left over from CRTs where the beam needed time to fly back.

## 2. Picking the numbers

VESA 800×600 @ 60 Hz:

|  | visible | front | sync | back | total |
|---|---|---|---|---|---|
| horizontal (pixels @ 40 MHz) | 800 | 40 | 128 | 88 | 1056 |
| vertical (lines) | 600 | 1 | 4 | 23 | 628 |

40 MHz is too fast for breadboarded 74LS logic. But the monitor only checks the
**sync timing**, not how many pixels you send. Use a **10 MHz** clock and divide
the horizontal numbers by 4:

```
horizontal: 200 + 10 + 32 + 22 = 264 clocks per line
line rate   = 10 MHz / 264  = 37.879 kHz   ✔ same as VESA
frame rate  = 37.879k / 628 = 60.32 Hz     ✔
```

Then the image resolution: 200 clocks across, and each **image pixel** is 2 clocks
wide (8 real pixels) and 8 lines tall (8 real pixels). That gives **100 × 75** with square pixels.

## 3. Counting position

- **H counter**: counts clocks 0 → 263, then back to 0. Needs 9 bits → three
  4-bit counters (74LS163).
- **V counter**: counts lines 0 → 627. 10 bits → three more '163s. It only
  advances when the H counter wraps (`lineEnd` drives its enable pins).

**Why 74LS163 instead of '161:** the '163 clears *synchronously* (on the next clock
edge), the '161 *asynchronously* (immediately). With an async clear you decode 264,
the counter shows 264 for a few nanoseconds and then resets. That's a glitch, and
every gate decoding the counter can see it. With a synchronous clear you decode the
last value (263) and the counter simply goes to 0 on the next edge, so there's no
glitch. The same principle runs through everything below: **keep it synchronous.**

## 4. Making the signals: J-K flip-flops

Each output (hsync, vsync, hdisplay, vdisplay) is a J-K flip-flop on the 10 MHz clock:
**J** sets it, **K** resets it, both only at a clock edge. A flip-flop changes on
the edge after it sees J or K, so to switch at count N you decode **N − 1**.

```
hsync:    J at 209  → on at 210      K at 241 → off at 242     (32 clocks = 3.2 µs)
vsync:    J at 600  → on at 601      K at 604 → off at 605     (gated by lineEnd)
```

Since the outputs come straight from flip-flops, they're clean even if a decoder
glitches between edges.

## 5. Decoding: which bits to AND

"Count = 209" with every bit checked needs a 9-input AND with inverters for the
0-bits. Fewer inputs are possible because:
1. the counter never exceeds 263, so many bit patterns never happen;
2. a flip-flop ignores "set" while it's already set, so firing again is harmless
   *as long as it doesn't fire at the wrong moment*.

**The tempting shortcut**, AND only the 1-bits, fails for hsync:

```
J: 209 = 0 1101 0001   1-bits {7,6,4,0}
K: 241 = 0 1111 0001   1-bits {7,6,5,4,0}   ← contains all of J's bits
```
At count 241 **both** J and K fire, and J = K = 1 makes a J-K flip-flop *toggle*.
hsync goes wrong. The fix is to add `/Q5` to J (241 has bit 5 set, 209 doesn't).

`vga_timing.py` does this search automatically: start from full decoding, remove
inputs one at a time, and keep a removal only if a simulated full cycle still gives
exactly the right waveform. The resulting wiring table is in the
[card README](../hardware/vga-card/README.md); the tests include the hsync failure
above, so the reason for the extra input is recorded as a check.

## 6. Pixels: addressing the EEPROM

```
x = hcount bits 7..1   (drop bit 0: each image pixel is 2 clocks)
y = vcount bits 9..3   (drop bits 0–2: each image pixel is 8 lines)
address = y·128 + x    →  A6..A0 = x,  A13..A7 = y
```
No arithmetic at all: dividing by 2 or 8 is just *which wires you connect*. The
row stride is 128 rather than 100 for the same reason, and x = 100..127 is simply
never displayed.

## 7. The EEPROM is too slow, so pipeline it

A 28C256 takes up to **150 ns** to output data after its address changes. One image
pixel lasts **200 ns**. If the EEPROM drives the DAC directly, the first ~3/4 of
every pixel shows the *previous* pixel's data or garbage in between.

Fix: a **74HCT374** register between the EEPROM and the DAC. At the end of each
image pixel (when the H count goes odd → even) it grabs the EEPROM's output, which
has been stable for 200 ns, longer than the 150 ns access time. It shows that during
the next pixel, so the picture is clean but 2 clocks late. The display window is
shifted 2 clocks to match (`hdisplay` = 2…201 instead of 0…199). This is the
same idea as a CPU pipeline: add a register, gain time, pay in latency.

**Blanking for free:** colour must be 0 V outside the visible area. The '374 has a
tri-state `/OE`; `NAND(hdisplay, vdisplay)` drives it, and when the outputs are off,
the monitor's 75 Ω termination pulls the colour lines to 0 V.

**Why HCT:** its inputs accept the LS logic levels feeding it, and its CMOS outputs
can hold ≈ 4.5 V while driving the DAC's ~6 mA. LS outputs sag badly at that current.

## 8. The DAC: bits → voltage

Each colour has 2 bits → 4 levels. Two resistors into the monitor's 75 Ω, the MSB's
resistor half the LSB's:

```
Q(MSB) ──[ R ]──┬──► monitor input (75 Ω to ground)
Q(LSB) ──[ 2R ]─┘
```

Full scale (both bits high at V_H ≈ 4.5 V) should be 0.7 V. With both high, R ∥ 2R = 2R/3
forms a divider with 75 Ω:

```
4.5 · 75 / (75 + 2R/3) = 0.7   →   R ≈ 611 Ω   →  620 Ω and 1.2 kΩ (standard values)
```

The exact levels (Millman's theorem: V = ΣVᵢ/Rᵢ ÷ Σ1/Rᵢ, a low output counts as 0 V):
**0, 0.24, 0.46, 0.70 V**, almost perfectly evenly spaced.

6 bits per pixel = 2 R + 2 G + 2 B = **64 colours**; byte layout `00RRGGBB`.

## 9. The picture: `image_to_rom.py`

1. crop to 4:3, centred
2. shrink to 100 × 75 by averaging blocks of source pixels (box filter)
3. round each channel to 0–3 (optionally with a 4×4 **Bayer dither**, which trades
   resolution for apparent colour depth)
4. write `00RRGGBB` at `y·128 + x`

It has its own small PNG decoder (`png.py`, standard library only), and a built-in
test pattern (colour bars, grey ramp, a circle on a hue sweep) so the card can be
tested without any image.

## 10. Verified by simulation: `vga_sim.py`

The whole card is stepped one 10 MHz edge at a time, with the *generated* decoders:

```
hsync runs (clock)   [(210, 32)]       ← 3.2 µs pulse after a 1 µs front porch
vsync runs (line)    [(601, 4)]
line rate kHz        37.879
frame rate Hz        60.317
lit rows             (0, 599)
lit cols             (2, 201)          ← shifted by the pixel latch, as designed
```
…and it renders what the monitor would show (`build/frame.png`). The test suite
checks the frame pixel by pixel against the ROM and checks blanking everywhere else.

## 11. Build order on the breadboard

1. **Oscillator** → check 10 MHz on a scope.
2. **H counter + hsync** → scope: 37.88 kHz, 3.2 µs pulses.
3. **V counter + vsync** → plug in a monitor: even with a black screen, its
   on-screen info should report *800×600 60 Hz*. That's the proof the timing is
   right, before any colour exists.
4. **hdisplay/vdisplay** → tie the colour lines high through the DAC: a solid white rectangle filling the screen.
5. **EEPROM + '374 + DAC** → the picture.

Keep 10 MHz wires short, decouple every chip, and use a common ground everywhere.
At this speed, breadboard capacitance and ringing start to matter.

## Check yourself

1. Why is the frame rate the same at 10 MHz as at 40 MHz?
2. What would the monitor do if hsync were inverted?
3. Why decode 263 (not 264) for the counter clear?
4. Without the '374, why would the picture look smeared to the right?

<details><summary>Answers</summary>

1. Every horizontal time was divided by 4 along with the clock period, so each line still lasts 26.4 µs and there are still 628 lines.
2. 800×600@60 specifies positive sync. Many monitors detect the polarity, but some would fail to lock or pick the wrong mode.
3. The '163 clears on the *next* edge: decode 263, and the count after 263 is 0.
4. Each pixel would show the previous pixel's data for up to 150 ns of its 200 ns, so colours appear late, i.e. shifted right, with mixed edges.
</details>
