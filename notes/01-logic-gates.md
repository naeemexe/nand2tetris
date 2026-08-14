# 01 — Logic gates (project 1)

**Goal:** starting from a single given gate, Nand, build every gate the
computer needs: Not, And, Or, Xor, Mux, DMux, their 16-bit versions, and the
multi-way versions.

## 1. Why Nand is enough

| a | b | Nand |
|---|---|---|
| 0 | 0 | 1 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

Nand is *functionally complete*: any truth table can be built from it. The proof
is simply the first three chips below, because with Not, And and Or you can write
any boolean function as an Or of Ands (one And-term per row of the truth table
where the output is 1).

## 2. HDL in five minutes

```hdl
CHIP And {
    IN a, b;          // input pins
    OUT out;          // output pins
    PARTS:            // the wiring: instances of other chips
    Nand(a=a, b=b, out=nandAB);        // nandAB is an internal wire, made on first use
    Nand(a=nandAB, b=nandAB, out=out);
}
```

- `a=x` means "the part's pin `a` is connected to my wire `x`". Left side = the
  part's pin, right side = this chip's wire.
- Buses: `IN a[16]`, sub-buses `a[0..7]`, single bits `a[3]`. The constants `true`
  and `false` fill whole buses.
- An **internal** wire can't be indexed (`x[3]` only works on the chip's own
  pins). If you need part of an internal bus, split it when you create it:
  `out[0..7]=low, out[8..15]=high` (the ALU uses this).
- Order of the PARTS doesn't matter. This is a wiring diagram, not a program.

**Testing:** each chip has `X.tst` (a script that sets inputs and records outputs
to `X.out`) and `X.cmp` (the correct outputs). `tools/HardwareSimulator.sh X.tst`
prints *"Comparison ended successfully"* when `.out` equals `.cmp`.

## 3. Building up, one gate at a time

### Not
`Nand(a=in, b=in)`. With both inputs equal, Nand is 1 exactly when `in` is 0.

### And
`Not(Nand(a, b))`, i.e. two Nands. (The `And.hdl` here writes the Not as a
second Nand with both inputs tied together.)

### Or: De Morgan
De Morgan's law: **`a OR b = NOT( NOT a AND NOT b )`**, which is
`Nand(Not a, Not b)`. That's three Nands:

```
a ──Nand(a,a)──┐
               Nand ── out
b ──Nand(b,b)──┘
```

### Xor
`a XOR b` is 1 when the inputs differ. The classic 4-Nand version shares
`n = Nand(a,b)`:  `out = Nand( Nand(a, n), Nand(n, b) )`. The 5-Nand version in
`Xor.hdl` also works; finding the 4-gate one is a nice exercise.

### Mux: the selector
`out = a if sel = 0, else b`. As a formula: **`(a AND NOT sel) OR (b AND sel)`**.

Built straight from Nands (`Mux.hdl`): an Or-of-Ands is a Nand-of-Nands, by De
Morgan again, so

```
selNot = Nand(sel, sel)
aPick  = Nand(a, selNot)     // 0 only when a=1 and sel=0
bPick  = Nand(b, sel)        // 0 only when b=1 and sel=1
out    = Nand(aPick, bPick)  // 1 if either "pick" fired
```

Four Nands, versus about seven if you chain the separate Not/And/Or chips.

### DMux: the router
The opposite of a Mux: one input, two outputs; `sel` decides which output gets
`in`, and the other gets 0.
`a = in AND NOT sel`, `b = in AND sel`.

## 4. Going wide: 16-bit chips

`Not16`, `And16`, `Or16` and `Mux16` are just 16 copies of the 1-bit chip, one per
bit, with `sel` shared by all 16 Muxes. Nothing new in the logic, and it's the
first taste of the **bus**: a group of wires treated as one number.

## 5. Going multi-way: trees

**Or8Way**: is any of 8 bits set? Pairs → pairs of pairs → final Or. A tree has
depth log2(8) = 3 gates, while a chain would have depth 7. Depth is delay, and
in real hardware, delay limits clock speed.

**Mux4Way16**: pick 1 of 4 buses with a 2-bit `sel`. Two levels of Mux:

```
a ─┐
   Mux(sel[0]) ─┐
b ─┘            │
                Mux(sel[1]) ── out
c ─┐            │
   Mux(sel[0]) ─┘
d ─┘
```

The **low** select bit chooses within a pair (a/b, c/d) and the **high** bit
chooses between pairs, which matches the binary numbering a=00, b=01, c=10, d=11.
Mux8Way16 adds a third level for `sel[2]`.

**DMux4Way / DMux8Way** use the same tree, opened from the other end:
split by the **high** bit first (top half or bottom half), then by the lower
bits inside each half. `DMux8Way` = one DMux on `sel[2]` + two `DMux4Way` on `sel[0..1]`.

## 6. What to remember

- Everything is Nand underneath, and De Morgan's laws turn And/Or forms into Nand forms.
- Mux = choose (used for reading memory), DMux = route (used for writing memory).
- Wide chips are copies; multi-way chips are trees. Trees keep the delay down.

## Check yourself

1. Build Or from Nand without looking. Which law are you using?
2. Why does Mux4Way16 use `sel[0]` at the first level and not `sel[1]`?
3. How many Nand gates deep is the critical path of Or8Way built from Or chips?
4. What would go wrong if you tried `Or8Way(in=someInternalBus[0..7])`?

<details><summary>Answers</summary>

1. De Morgan: `a OR b = Nand(NOT a, NOT b)`, so 3 Nands.
2. The two levels have to agree with binary numbering: `sel[0]` decides between neighbours (00/01, 10/11), `sel[1]` between the pairs. Swapping them gives a working chip that picks the wrong input.
3. Each Or is 2 Nands deep (the Nots in parallel, then the final Nand), and the tree has 3 levels, so 6.
4. Internal pins can't be sub-indexed. Split the bus where it's produced: `out[0..7]=someLow`.
</details>
