# From NAND to Tetris — and onto breadboards

A complete computer built from first principles, twice.

**1. The Nand2Tetris stack** (`projects/`): a 16-bit computer in HDL starting from a
single Nand gate, then all the software that makes it usable, each layer written
in this repo:

| | | |
|---|---|---|
| 1–3 | logic gates → ALU → RAM and program counter | HDL |
| 4 | programs in Hack assembly | Hack asm |
| 5 | CPU and the full Hack computer | HDL |
| 6 | assembler | Python |
| 7–8 | VM translator (stack machine → assembly) | Python |
| 9 | Snake, a game written in Jack | Jack |
| 10–11 | Jack compiler: tokenizer, parser, code generator | Python |
| 12 | operating system: heap, math, strings, graphics, text, keyboard | Jack |

End to end: Pong compiled by this compiler, against this OS, through this VM
translator and assembler, is 27,825 instructions and runs on the Hack CPU.

**2. Real hardware** (`hardware/`):

- **8-bit breadboard computer** of 74LS chips with 11 microcoded instructions in
  EEPROMs. Includes a microcode generator, a simulator that executes the actual
  EEPROM image, an assembler that outputs DIP-switch settings, example programs
  and an Arduino EEPROM programmer.
- **VGA video card** from discrete logic: 800×600 @ 60 Hz sync from a 10 MHz clock,
  a 100×75 image in 64 colours from an EEPROM through a resistor DAC. Includes the
  timing derivation, a decoder-logic generator, a clock-level simulator and an
  image converter.

## Learning notes

Start at **[notes/00-start-here.md](notes/00-start-here.md)**: one note per stage,
in build order, explaining why each piece works, with self-check questions.
The git history follows the same order, one step per commit
(`git log --reverse --oneline`).

## Run everything

```bash
python3 run_tests.py          # 98 checks: official test scripts + this repo's tests (needs Java)
python3 run_tests.py --quick  # skip the slower OS tests
```

## Credits

- *The Elements of Computing Systems* by Noam Nisan and Shimon Schocken
  ([nand2tetris.org](https://www.nand2tetris.org)): the Hack platform, project
  specifications, test scripts and the tools in `tools/`.
- Ben Eater ([eater.net/8bit](https://eater.net/8bit), [eater.net/vga](https://eater.net/vga)):
  the breadboard computer design and the discrete-logic video card idea.
