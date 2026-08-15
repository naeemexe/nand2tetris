# 05 — The computer (project 5)

**Goal:** wire the ALU, registers, PC and RAM into a CPU that executes Hack
machine code, then into a complete computer.

## 1. Instruction encoding

```
A-instruction:  0 v v v v v v v v v v v v v v v        (value, 15 bits)
C-instruction:  1 1 1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
bit index:     15 . . 12 11 10  9  8  7  6  5  4  3  2  1  0
```

- `a`: the ALU's second operand is A (a=0) or M (a=1)
- `c1..c6`: **exactly the ALU's** `zx nx zy ny f no`. The instruction set was
  designed around the ALU, so decoding is just wiring.
- `d1 d2 d3`: store the result in A, D, M
- `j1 j2 j3`: jump if result < 0, = 0, > 0 (any combination)

Example: `D=D+M` → `111 1 000010 010 000` (a=1, comp D+M, dest D, no jump).

## 2. The CPU, piece by piece (`projects/5/CPU.hdl`)

```
              instruction
                  │
      ┌───────────┴──── isC = instruction[15]
      ▼
   Mux16(instruction | ALU out, sel=isC) ─► A register ─┬─► addressM, PC.in
                                                         │
   inM ─────────────────────────────┐                   │
                       Mux16(A | M, sel=a) ◄─────────────┘
                                    │
   D register ─────────────► ALU(x=D, y=A/M) ─► outM, D.in, A.in
                               │ zr, ng
                               ▼
                         jump logic ─► PC(load=jump, inc=1, reset)
```

Decisions, one at a time:

1. **What goes into A?** An A-instruction loads the instruction itself; a
   C-instruction with `d1` loads the ALU result. So `Mux16(sel=isC)`, and
   `loadA = isA OR (isC AND d1)`.
2. **D** loads the ALU result when `isC AND d2`.
3. **writeM** = `isC AND d3`. Every control signal is ANDed with `isC`, because an
   A-instruction's low bits are data and must not be read as d/j bits.
4. **ALU's y input** = `Mux16(A, inM, sel=a)`.
5. **Jump**: the ALU already reports `zr` and `ng`, so "positive" = `NOT(zr OR ng)`.
   ```
   jump = isC AND ( (j1 AND ng) OR (j2 AND zr) OR (j3 AND pos) )
   ```
   `0;JMP` has all three j bits set, so it always matches.
6. **PC**: `in = A`, `load = jump`, `inc = true`, plus `reset`. The PC's own priority
   (reset > load > inc) does the rest.

## 3. Memory map (`Memory.hdl`)

Decided entirely by the top 2 address bits:

| address[14] | address[13] | range | goes to |
|---|---|---|---|
| 0 | x | 0x0000–0x3FFF | RAM16K |
| 1 | 0 | 0x4000–0x5FFF | Screen (8K) |
| 1 | 1 | 0x6000 | Keyboard |

Same pattern as RAM: DMux the load by those bits, Mux4Way16 the outputs.

## 4. Computer

```
ROM32K(address=pc) ─► instruction ─► CPU ─► addressM/outM/writeM ─► Memory
                                      ▲                                │
                                      └──────────── inM ◄──────────────┘
```

Three parts. Fetch, decode and execute all happen in **one** clock cycle: the
"fetch" is just ROM outputting the word at `pc` combinationally. (The breadboard
computer in note 10 takes 5 clock steps per instruction instead, using microcode.)

## 5. A full check

`CPU.tst` also passes with the CPU built entirely from this repo's chips (ALU,
PC and registers from projects 2–3, down to Nand), not just with the simulator's
built-in versions. All the chips in one folder, one test run.

## Check yourself

1. Encode `AM=M-1`.
2. Why must `writeM` be ANDed with `isC`?
3. `D;JGE`: which j bits, and what does the jump logic compute for D = 0?

<details><summary>Answers</summary>

1. comp `M-1` = a=1, 110010; dest AM = 101; → `1111110010101000`.
2. For an A-instruction, bit 3 is just part of the constant; without the AND, `@8` would write memory.
3. `j = 011`. D = 0 → zr = 1 → `j2 AND zr` = 1 → jump.
</details>
