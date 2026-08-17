# 00 — Start here

These notes walk through the whole project one layer at a time, in the same order
it was built. Each note explains **why** each piece works, not just what to type,
and ends with questions to test yourself.

## The big picture

```
  Snake.jack, Pong.jack          high-level program            (project 9)
        │  Jack compiler          tokenizer → parser → codegen  (projects 10–11)
        ▼
  push local 0 / call ...        stack-machine VM code
        │  VM translator                                         (projects 7–8)
        ▼
  @SP  AM=M-1  D=M ...           Hack assembly
        │  assembler                                             (project 6)
        ▼
  1110001100001000               binary machine code
        │  runs on
        ▼
  CPU  ←→  RAM  ←→  Screen/Keyboard   the Hack computer           (project 5)
   ALU, registers, PC                                           (projects 2–3)
   And, Or, Mux, DMux ...                                       (project 1)
   Nand                          the only thing we're given

  + the OS (Math, Memory, Screen, Output, ...) written in Jack (project 12)
```

Then the same ideas built for real, with chips on breadboards:

```
  8-bit computer  — bus, registers, ALU, RAM, microcoded control in EEPROMs
  VGA card        — counters + gates make video timing; an EEPROM holds the picture
```

## Reading order

| Note | Covers | Code |
|---|---|---|
| [01 — Logic gates](01-logic-gates.md) | Nand → every other gate, Mux/DMux | `projects/1` |
| [02 — Arithmetic & the ALU](02-alu.md) | binary addition, two's complement, the ALU | `projects/2` |
| [03 — Memory](03-memory.md) | DFF → Bit → Register → RAM, the PC | `projects/3` |
| [04 — Machine language](04-machine-language.md) | Hack assembly, Mult, Fill | `projects/4` |
| [05 — The computer](05-computer.md) | CPU, memory map, the full machine | `projects/5` |
| [06 — Assembler](06-assembler.md) | symbols, two passes | `projects/6` |
| [07 — VM translator](07-vm-translator.md) | stack machine, segments, call/return | `projects/7`, `8` |
| [08 — Jack compiler](08-compiler.md) | tokenizer, recursive descent, codegen, Snake | `projects/9`–`11` |
| [09 — Operating system](09-operating-system.md) | heap, fast math, drawing, text | `projects/12` |
| [10 — 8-bit breadboard computer](10-8bit-computer.md) | real chips, bus, microcode | `hardware/8bit-computer` |
| [11 — VGA card](11-vga-card.md) | video timing, decoding, DAC | `hardware/vga-card` |

## How to study this repo

**Follow the commits.** Each commit is one step (one chip group, one tool, one OS
class), and its message explains the idea:

```bash
git log --reverse --oneline        # the whole build, in order
git show <hash>                    # one step: the message + exactly what changed
```

**Run things.** Every stage has a check, and seeing it pass (or breaking it on
purpose and watching it fail) teaches more than reading:

```bash
python3 run_tests.py --quick                               # everything except the slow OS tests
tools/HardwareSimulator.sh projects/2/ALU.tst              # one chip
python3 hardware/8bit-computer/sim8.py hardware/8bit-computer/programs/add.asm --trace
```

**Rebuild it yourself.** The best test of understanding is a fresh branch from
the first commit where you rebuild each step without looking, then `git diff`
against this one.

## Credits

- *The Elements of Computing Systems* (Nisan & Schocken) and nand2tetris.org: the
  Hack platform, the project specs, the test scripts and the tools in `tools/`.
- Ben Eater (eater.net/8bit, eater.net/vga): the breadboard computer and the idea
  of a discrete-logic video card. The tools, simulators and design changes in
  `hardware/` are this repo's own and are explained in notes 10 and 11.
