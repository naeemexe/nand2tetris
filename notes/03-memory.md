# 03 — Memory (project 3)

**Goal:** make circuits that *remember*. Everything so far was combinational:
the outputs depend only on the current inputs. Now we add **time**.

## 1. The clock and the DFF

A clock is a signal ticking 0,1,0,1… Each tick+tock is one *time step* `t`.

The only new primitive is the **DFF** (data flip-flop): `out(t) = in(t−1)`. It
outputs whatever its input was one step ago. Everything that remembers is built
from it.

Why we need a clock at all: gates have delays, so after an input changes the
outputs briefly flicker through wrong values. The clock says "only look at
values at the tick, once everything has settled". That is the *synchronous
design* idea, and it comes back in the breadboard computer and the VGA card.

## 2. Bit: remembering forever

A DFF forgets after one step. To keep a value, feed its output back to its own
input. To be able to *change* it, put a Mux in that loop:

```
          load
           │
in ──────►│Mux│───► DFF ──┬──► out
      ┌──►│   │           │
      └───────────────────┘   (feedback: "keep the old value")
```

- `load = 0`: the Mux sends the DFF its own output, so the value is kept.
- `load = 1`: the Mux sends `in`, which is stored at the next tick.

## 3. Register

16 Bits side by side, all sharing one `load`, store one 16-bit word.

## 4. RAM: addressing

**RAM8** = 8 Registers + a way to write one and read one:

- **write**: `DMux8Way(in=load, sel=address)` delivers the load signal to exactly
  one register. All 8 see the same `in`, but only one is told to load it.
- **read**: all 8 registers output all the time; `Mux8Way16(sel=address)` picks one.

That pattern (**DMux the load, Mux the outputs**) is the whole idea of memory.
Bigger RAMs repeat it recursively:

| chip | built from | address bits | high bits pick… | low bits go to… |
|---|---|---|---|---|
| RAM8 | 8 Register | 3 | the register | – |
| RAM64 | 8 RAM8 | 6 | `[3..5]` the RAM8 | `[0..2]` inside it |
| RAM512 | 8 RAM64 | 9 | `[6..8]` | `[0..5]` |
| RAM4K | 8 RAM512 | 12 | `[9..11]` | `[0..8]` |
| RAM16K | 4 RAM4K | 14 | `[12..13]` (4-way!) | `[0..11]` |

Reading is instant (combinational), writing takes effect on the next tick:
`out(t) = RAM[address(t)](t)`.

## 5. Program counter

The PC holds the address of the next instruction. Each tick it does one of:

```
if reset:     out = 0          (highest priority)
else if load: out = in         (a jump)
else if inc:  out = out + 1    (normal flow)
else:         out = out
```

Implementation: compute the candidate next value with a **chain of Muxes**:

```
current ─► Mux(inc: current / current+1) ─► Mux(load: … / in) ─► Mux(reset: … / 0) ─► Register(load=true)
```

The **last Mux in the chain wins**, so the chain order *is* the priority order.
The register is always loaded, and when nothing is asserted the "new" value is just
the current one again.

## 6. What to remember

- DFF + feedback Mux = memory. All memory is that, repeated.
- Address decoding = DMux on write, Mux on read.
- A chain of Muxes implements priority (later = stronger).

## Check yourself

1. Why does the Bit need a Mux? What happens with a bare feedback loop and no Mux?
2. In RAM64, which address bits pick the RAM8, and why those and not the low ones?
3. Swap the order of the `load` and `reset` Muxes in the PC. What breaks?

<details><summary>Answers</summary>

1. With bare feedback the value never changes: there's no way in. The Mux is the "door".
2. The high bits `[3..5]`. Either choice gives working storage, but with high bits picking the bank, consecutive addresses stay in the same RAM8, which is the convention every test and the CPU assume.
3. `load` would beat `reset`: a jump in the same cycle as reset would go to the jump address instead of 0.
</details>
