# 06 — The assembler (project 6)

**Goal:** translate Hack assembly to binary. The first piece of *software* in the
stack (`projects/6/hack_assembler.py`).

## 1. Three jobs

1. **Parse**: drop comments (`//…`) and whitespace; classify each line as a
   label `(X)`, an A-instruction `@x`, or a C-instruction `dest=comp;jump`.
2. **Translate**: look up bit patterns in three tables (comp → 7 bits including
   `a`, dest → 3 bits, jump → 3 bits).
3. **Resolve symbols**: turn names into numbers.

## 2. Splitting a C-instruction

`dest` and `jump` are both optional:

```python
dest, _, rest = instr.rpartition("=")   # no "=" -> dest = ""
comp, _, jump = rest.partition(";")     # no ";" -> jump = ""
```

The dest bits don't need a table: `d1 d2 d3` = "is A / D / M in the string", so
`MD` and `DM` both work.

## 3. Symbols and why it takes two passes

Three kinds of symbols:
- **predefined**: `R0–R15`, `SP LCL ARG THIS THAT` (= 0–4), `SCREEN`, `KBD`
- **labels** `(LOOP)`: the ROM address of the next real instruction
- **variables**: any other `@name`, given RAM addresses 16, 17, 18… in order of first use

The problem: `@END` can appear *before* `(END)` is declared. When you see it
you don't know whether it's a label (defined later) or a new variable. So:

- **pass 1** walks the program counting real instructions and records every label's
  address. Labels emit no code, so they don't count.
- **pass 2** translates. Any symbol still unknown must be a variable, so it gets the next RAM slot.

## 4. Verified

For every `.asm` in projects 4 and 6 (including Pong, 27,483 instructions), the output
is byte-for-byte identical to the official assembler. `run_tests.py` checks this.

## 5. What to remember

- Assembly → binary is mostly table lookup; the only real thinking is symbols.
- Forward references are why assemblers (and linkers) make two passes.

## Check yourself

1. Variables start at 16. Why not 0?
2. What happens if a program uses `@i` once but never declares `(i)`?
3. In `Max.asm` vs `MaxL.asm`, what's different, and why is the output identical?

<details><summary>Answers</summary>

1. 0–15 are R0–R15 (and SP, LCL, … alias 0–4), reserved for the programmer and later the VM.
2. It becomes a variable at the next free RAM address. That's the intended behaviour.
3. `MaxL` has no symbols (labels/variables already replaced by numbers). Same program, so same binary.
</details>
