# 8-bit breadboard computer

A SAP-style 8-bit computer built from 74LS-series logic on breadboards, following
Ben Eater's series ([eater.net/8bit](https://eater.net/8bit)). The hardware design
is his; the software in this folder (microcode generator, simulator, assembler,
EEPROM programmer, display ROM) is written from scratch for this repo, and the
step-by-step explanation is in [`notes/10-8bit-computer.md`](../../notes/10-8bit-computer.md).

```
            ┌──────── 8-bit bus ────────┐
  Clock ──► │  PC (4-bit)    A register │ ──┐
            │  MAR (4-bit)   ALU (+/-)  │   │ carry, zero
            │  RAM 16 bytes  B register │   ▼
            │  IR            Output     │  Flags ──► Control EEPROMs ──► 16 control signals
            └───────────────────────────┘                ▲
                 IR opcode (4 bits) + step counter (3 bits) ┘
```

## Modules and chips

| Module | What it does | Main chips |
|---|---|---|
| Clock | astable (auto), monostable (single-step) and bistable (switch debounce) 555s, plus halt gating | 3× 555, 74LS00/04/08/32 |
| A, B registers | 8-bit latches; A and the ALU result can drive the bus | 2× 74LS173 + 74LS245 each |
| ALU | adds or subtracts (XOR inverts B, carry-in = 1) | 2× 74LS283, 2× 74LS86, 74LS245 |
| RAM + MAR | 16 bytes; program mode lets DIP switches set address/data | 2× 74189, 74LS173, 4× 74LS157, 74LS04 |
| Program counter | 4-bit counter with load (jumps) | 74LS161, 74LS245 |
| Instruction register | opcode (high nibble) to control logic, operand (low nibble) to the bus | 2× 74LS173, 74LS245 |
| Output | 8-bit register + EEPROM decoder + 4 multiplexed 7-segment digits | 74LS273, 28C16, 555, 74LS107, 74LS139 |
| Control logic | step counter + two microcode EEPROMs | 74LS161, 74LS138, 2× 28C16 |
| Flags | carry and zero latched by FI | 74LS173, 74LS02/08 |

## Instruction set (11 instructions)

| Opcode | Mnemonic | Does | Micro-steps after fetch |
|---|---|---|---|
| 0000 | NOP | nothing | – |
| 0001 | LDA a | A = RAM[a] | IO MI · RO AI |
| 0010 | ADD a | A = A + RAM[a], set flags | IO MI · RO BI · EO AI FI |
| 0011 | SUB a | A = A − RAM[a], set flags | IO MI · RO BI · EO AI SU FI |
| 0100 | STA a | RAM[a] = A | IO MI · AO RI |
| 0101 | LDI n | A = n (0–15) | IO AI |
| 0110 | JMP a | PC = a | IO J |
| 0111 | JC a | jump if carry | IO J *(only when CF = 1)* |
| 1000 | JZ a | jump if zero | IO J *(only when ZF = 1)* |
| 1110 | OUT | display A | AO OI |
| 1111 | HLT | stop the clock | HLT |

Every instruction starts with the fetch: `CO MI` (T0) then `RO II CE` (T1).

## Control EEPROM address layout

```
A10  A9  A8  A7    A6..A3   A2..A0
 0   ZF  CF  chip  opcode   step
```
Both control EEPROMs hold the **same** 2 KB image; A7 is tied low on one chip
(control bits 15–8) and high on the other (bits 7–0).

## Files

| File | |
|---|---|
| `isa.py` | control signals + microcode table — the single source of truth |
| `microcode.py` | builds `build/microcode.bin` and the Arduino header |
| `display_rom.py` | builds the 7-segment decoder image (unsigned + two's complement modes) |
| `sim8.py` | cycle-level simulator that executes the **EEPROM image**, not the mnemonics |
| `asm8.py` | assembler; prints the DIP-switch settings for loading RAM by hand |
| `programs/` | add, add_sub, count, multiply, fibonacci, updown |
| `tests/` | runs every program on the simulator and checks the output |
| [`../eeprom-programmer/`](../eeprom-programmer/) | Arduino sketch that burns these images (shared with the VGA card) |

```bash
python3 microcode.py                       # print the microcode table, build the image
python3 asm8.py programs/multiply.asm      # what to set on the DIP switches
python3 sim8.py programs/fibonacci.asm     # run it
python3 sim8.py programs/add.asm --trace   # watch every micro-step on the bus
python3 tests/test_programs.py
```
