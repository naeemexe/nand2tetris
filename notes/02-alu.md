# 02 — Arithmetic & the ALU (project 2)

**Goal:** add binary numbers with gates, represent negative numbers, and build
the Hack ALU, one chip that computes 18 different functions selected by 6
control bits.

## 1. Adding one column: HalfAdder

Adding two bits gives a 2-bit answer:

| a | b | carry | sum |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 1 |
| 1 | 0 | 0 | 1 |
| 1 | 1 | 1 | 0 |

Look at the columns: `sum = a XOR b`, `carry = a AND b`. That's the whole chip.

## 2. Adding a column with a carry coming in: FullAdder

Three inputs (`a`, `b`, carry-in `c`). Add them in two steps, the same way you'd
do it by hand:

```
HalfAdder(a, b)        -> s1, c1
HalfAdder(s1, c)       -> sum, c2
carry = c1 OR c2       // they can't both be 1, so Or is enough
```

## 3. Adding 16-bit numbers: ripple carry

Chain 16 adders: each column's carry-out is the next column's carry-in.

```
bit 0: HalfAdder(a0, b0)          -> out0, c0
bit 1: FullAdder(a1, b1, c0)      -> out1, c1
...
bit 15: FullAdder(a15, b15, c14)  -> out15, (carry out is thrown away)
```

Throwing away the last carry means arithmetic is **modulo 2¹⁶**: 65535 + 1 = 0.
It's called "ripple" because the carry has to travel through all 16 stages before
the top bit is correct, which makes it simple but slow. (Real CPUs use carry-lookahead.)

**Inc16** is just `Add16(in, 1)`: the constant 1 is written as
`b[0]=true, b[1..15]=false`.

## 4. Negative numbers: two's complement

In 16 bits, **−x is represented as 2¹⁶ − x**. In practice:

> to negate: flip all the bits, then add 1      (−x = !x + 1)

| decimal | 16-bit |
|---|---|
| 1 | 0000 0000 0000 0001 |
| 0 | 0000 0000 0000 0000 |
| −1 | 1111 1111 1111 1111 |
| −2 | 1111 1111 1111 1110 |
| 32767 | 0111 1111 1111 1111 |
| −32768 | 1000 0000 0000 0000 |

Why this encoding wins:
- **The adder doesn't care.** `x + (−y)` with the ordinary adder gives `x − y`.
  You get subtraction for free.
- **The top bit is the sign.** `bit 15 = 1` ⟺ negative. The ALU's `ng` output is
  literally `out[15]`.
- One zero (not +0 and −0), and the range is −32768 … 32767.

## 5. The ALU

Inputs `x`, `y` (16-bit) and six control bits, processed in order:

```
if zx: x = 0        if zy: y = 0
if nx: x = !x       if ny: y = !y
if f:  out = x + y   else: out = x & y
if no: out = !out
zr = (out == 0)     ng = (out < 0)
```

Implementation (`ALU.hdl`) is those four stages as Mux16s: compute both
options at each stage, and let the control bit pick.
- "zero it" = `Mux16(a=x, b=false, sel=zx)`
- "maybe flip it" = `Not16` + `Mux16`
- `f` picks between `Add16` and `And16`
- `zr` = no bit set anywhere = `Not(Or(Or8Way(low), Or8Way(high)))`
- `ng` = `out[15]`

### How 6 bits make 18 functions: worked examples

| zx nx zy ny f no | out | why |
|---|---|---|
| 1 0 1 0 1 0 | 0 | 0 + 0 |
| 1 1 1 1 1 1 | 1 | !( !0 + !0 ) = !(−1 + −1) = !(−2) = 1 |
| 0 0 1 1 0 0 | x | x & !0 = x & 1111… = x |
| 0 0 1 1 0 1 | !x | flip of the above |
| 0 0 1 1 1 1 | −x | !(x + −1) = !(x − 1) = −x (since !v = −v − 1) |
| 0 1 1 1 1 1 | x + 1 | !( !x + −1 ) = !(−x − 1 − 1) = x + 1 |
| 0 1 0 0 1 1 | x − y | !( !x + y ) = !(−x − 1 + y) = x − y |
| 0 1 0 1 0 1 | x \| y | !( !x & !y ) = x \| y — De Morgan again |

The identity behind most rows: **`!v = −v − 1`** (from `−v = !v + 1`).

## 6. What to remember

- `sum = XOR`, `carry = AND`; full adder = 2 half adders.
- Two's complement makes subtraction "add the negation", and negation "flip + 1".
- The ALU computes every option in parallel; control bits only *select*. That's
  the general pattern of hardware: do everything, Mux the answer.

## Check yourself

1. What is 0111 1111 1111 1111 + 1 in 16 bits, as a signed number?
2. Show that `zx=0 nx=0 zy=0 ny=1 f=1 no=1` computes `y − x`… or does it? Work it out.
3. Why can `zr` and `ng` never both be 1?

<details><summary>Answers</summary>

1. 1000 0000 0000 0000 = −32768. The sum overflowed past the largest positive number.
2. It computes `!(x + !y) = −(x + !y) − 1 = −(x − y − 1) − 1 = y − x`. Yes.
3. `ng` means bit 15 is set, and if any bit is set the value isn't zero.
</details>
