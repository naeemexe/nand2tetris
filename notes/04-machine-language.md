# 04 — Machine language (project 4)

**Goal:** program the Hack computer directly in its assembly language before
building it, so the CPU design in project 5 has a clear target.

## 1. The machine as a programmer sees it

- **A**: address/data register. **D**: data register. **M**: the RAM word at
  address A (`M` *means* `RAM[A]`).
- ROM holds the program; the PC walks through it.
- RAM: `0–15` are also called `R0–R15`, `16384` = `SCREEN`, `24576` = `KBD`.

Only two instruction kinds:

```
@value          A-instruction: A = value   (15-bit constant or a symbol)
dest=comp;jump  C-instruction: compute, store, maybe jump
```

`comp` is anything the ALU can do with D and A (or M): `0, 1, -1, D, A, !D, D+1,
D-A, D&M, …`. `dest` is any of A, D, M. `jump` compares the result with 0:
`JGT JEQ JGE JLT JNE JLE JMP`.

**Idiom:** `@X` then use `M` = "read/write variable X". `@LABEL` then `0;JMP` =
"goto LABEL". There's only one address register, so you're forever loading A.

## 2. Mult: R2 = R0 × R1

No multiply instruction, so use repeated addition:

```
R2 = 0
count = R1
while count > 0:  R2 += R0;  count -= 1
```

Assembly patterns used (see `projects/4/mult/Mult.asm`):
- **a variable**: `@count` gives a new symbol that the assembler places at RAM[16]
- **a loop**: `(LOOP)` label at the top, `@LOOP 0;JMP` at the bottom
- **a conditional exit**: load the value into D, `@END`, `D;JLE`
- **halt**: Hack has no halt, so the program ends in `(END) @END 0;JMP`, an
  intentional infinite loop.

## 3. Fill: memory-mapped I/O

The screen is 256 rows × 512 pixels, one bit each: 8192 words from
`SCREEN` (16384). Writing `-1` (all ones) to a word blackens 16 pixels.
The keyboard is a single word at `KBD` (24576) holding the code of the key
currently pressed, or 0.

Plan:
```
forever:
    color = (RAM[KBD] != 0) ? -1 : 0
    for addr = SCREEN .. KBD-1:  RAM[addr] = color
```

Key trick, a **pointer**: `addr` holds an address, so to write *where it points*:

```
@addr
A=M      // A = the address stored in addr
M=D      // RAM[that address] = D
```

That's exactly what `*p = value` compiles to in C. The screen ends right where
the keyboard begins, so `KBD` doubles as the loop's end marker.

## 4. What to remember

- `@` loads A; M is RAM[A]; a C-instruction is ALU + destination + jump.
- Variables are just named RAM addresses; labels are named ROM addresses.
- I/O is memory: drawing is writing RAM, reading keys is reading RAM.

## Check yourself

1. Write assembly for `if (D == 0) goto ZERO`.
2. Why does `Mult` use a copy `count` instead of decrementing R1 directly?
3. How many words does one screen row take, and where does row 10 start?

<details><summary>Answers</summary>

1. `@ZERO` then `D;JEQ`.
2. The test resets R0/R1 between runs and only checks R2, so either works. But not destroying your inputs is the good habit, and it's what a function would have to do.
3. 512 / 16 = 32 words; row 10 starts at 16384 + 10·32 = 16704.
</details>
