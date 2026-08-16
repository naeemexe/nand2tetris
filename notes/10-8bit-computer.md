# 10 — The 8-bit breadboard computer

**Goal:** build a working computer from real 74LS-series chips on breadboards,
module by module, following Ben Eater's series (eater.net/8bit). Everything from
notes 01–05 shows up again, except now gates have delays, wires pick up noise,
and the "control unit" is two EEPROMs full of microcode.

This note explains each module in build order, how to check it before moving on,
and how the software in `hardware/8bit-computer/` supports the build.

---

## How it differs from Hack

| | Hack (nand2tetris) | 8-bit breadboard computer |
|---|---|---|
| word size | 16 bits | 8 bits |
| memory | 32K ROM + 16K RAM | 16 bytes RAM, program and data together |
| connections | point-to-point wires | **one shared bus** |
| instruction timing | 1 clock per instruction | **5 clock steps** per instruction (microcode) |
| decoding | wiring of instruction bits | lookup table in EEPROMs |

---

## The bus: the central idea

Every module connects to the same 8 wires. At any moment **one** module puts a
value on the bus (its "out" signal) and any number of modules read it (their
"in" signals). Two modules driving at once means two outputs fighting:
garbage, heat, maybe damage.

How a module "lets go" of the bus: a **tri-state** driver (74LS245) has a third
output state, *disconnected* (high impedance), besides 0 and 1. Its `/OE` pin
decides. That's why nearly every module has a '245 between it and the bus.

---

## Module 1 — Clock

Everything happens on clock edges, so the clock comes first. Three 555 timers:

| 555 mode | job |
|---|---|
| astable | free-running clock, speed set by a potentiometer (≈1 Hz to a few hundred Hz) |
| monostable | single-step button: one clean pulse per press |
| bistable | the auto/manual switch, debounced |

**Debouncing:** a mechanical switch bounces for a few ms, which the logic would
see as dozens of edges. The 555s turn a bouncy contact into one clean transition.

A few gates (74LS08/32/04) select which source drives the clock, and an AND gate
with the inverted **HLT** signal stops the clock.

✅ *Check:* LED on the clock output blinks; single-step gives exactly one blink per press.

## Module 2 — Registers A and B (and the instruction register)

Each register is two 74LS173 (4-bit D registers) plus a 74LS245 to the bus.
- **Load:** the '173 latches its inputs on the rising clock edge *only when its
  load-enable pins are active*. That's the "AI"/"BI" signal. Same idea as
  `Bit = DFF + Mux` in note 03, but in a chip.
- **Output to bus:** the '173 outputs always feed the ALU and the LEDs; the '245
  decides whether they also go onto the bus ("AO").

The instruction register is the same, except only its **low 4 bits** can go to
the bus (the operand), and its **high 4 bits** go to the control logic (the opcode).

✅ *Check:* put a value on the bus by hand (with resistors or DIP switches), assert
"in", pulse the clock, and the LEDs hold the value after you remove it.

## Module 3 — ALU

Two 74LS283 4-bit adders chained = 8-bit adder. Subtraction without a
subtractor, using two's complement from note 02:

```
A − B = A + (NOT B) + 1
```

- 74LS86 XOR gates on B: `B XOR SU` flips every bit when SU = 1
- the adder's carry-in is tied to SU, which supplies the "+1"

Output to the bus through a '245 ("EO", Σ out). The ALU computes all the time;
EO only decides when the result is put on the bus. Same "compute everything,
select later" pattern as the Hack ALU.

✅ *Check:* load A and B, watch the sum LEDs; flip SU and watch the difference.

## Module 4 — RAM and the memory address register

- MAR: one 74LS173 holds a 4-bit address ("MI" loads it from the low bus bits).
- RAM: two 74189 (16 × 4 bits each). Their outputs are **inverted**, so 74LS04
  inverters restore the data before the '245.
- **Program mode:** 74LS157 multiplexers choose between the MAR/bus and the
  DIP switches for address and data, so you can type a program in by hand with a
  write button. It's the same Mux idea as note 01.

✅ *Check:* program mode → write a few bytes → run mode → read them back onto the bus.

## Module 5 — Program counter

A 74LS161 4-bit counter. Three controls, mirroring the Hack PC in note 03:
- **CE** count enable (`pc++`)
- **J** load from the bus (jump) — the '161's load beats counting
- **CO** put the PC on the bus (through a '245)

## Module 6 — Output display

A 74LS273 octal flip-flop holds the value. Four 7-segment digits show it in
decimal, and that's harder than it sounds: binary → decimal digits in logic
gates is a big circuit. Instead, an **EEPROM is used as a lookup table**:

```
address = mode (signed?) | which digit (2 bits) | value (8 bits)   →   data = segments to light
```

The digits share their 7 segment wires and take turns being lit (**multiplexing**):
a 555 clocks a 2-bit counter (74LS107), a 74LS139 enables one digit at a time and
also tells the EEPROM *which* digit to output. Above ~50 Hz per digit, persistence
of vision shows all four at once.

**In this repo:** `display_rom.py` generates that table (unsigned and two's complement,
leading zeros blanked) → `build/display.bin`.

## Module 7 — Control logic: microcode

This is where it becomes a CPU. Every instruction is a sequence of **micro-steps**,
and each step is a set of control signals that are on during that clock cycle.

**Fetch**, the same for every instruction:
```
T0:  CO MI       PC → bus → MAR           ("which address?")
T1:  RO II CE    RAM[MAR] → bus → IR, PC++ ("get the instruction")
```
Then the instruction's own steps, e.g. `ADD 14`:
```
T2:  IO MI       operand (14) → MAR
T3:  RO BI       RAM[14] → B
T4:  EO AI FI    A+B → A, latch the flags
```

Hardware:
- **step counter**: a 74LS161 clocked on the **inverted** clock, so control
  signals change on the falling edge and are stable before the rising edge
  when registers latch. Setup time again.
- a 74LS138 decodes the step for the LEDs and resets the counter at T5
- **two 28C16 EEPROMs**: address = (flags, opcode, step) → 16 control bits

```
A10  A9  A8  A7    A6..A3   A2..A0
 0   ZF  CF  chip  opcode   step
```
Both EEPROMs get the same image; A7 is tied low on one (bits 15–8) and high on
the other (bits 7–0).

**Active-low lines:** some chip inputs are active-low (the '245's `/OE`, the '173's
load enables, …). The microcode here is written active-high (1 = do it), and
each active-low control line passes through an inverter on the control board, as on
the schematic. If a module does the opposite of what you expect, check that inverter.

## Module 8 — Flags and conditional jumps

A 74LS173 latches two flags when **FI** is on:
- **CF** carry out of the adder
- **ZF** result is zero: NOR together all 8 sum bits

The flags feed **two more EEPROM address lines**. So the microcode for `JC` can be
*different* depending on the carry flag:

| instruction | CF = 0 | CF = 1 |
|---|---|---|
| JC addr | (nothing) | `IO J` |

That's the entire implementation of conditional jumps: four copies of the
microcode table, one per flag combination. No branching logic at all.

**Carry after SUB:** `A − B` is computed as `A + ~B + 1`, which carries out
exactly when there was **no borrow**, i.e. when `A ≥ B`. `multiply.asm` uses
this: `y − 1` sets carry while `y ≥ 1`, so `jc` means "keep looping".

---

## The software (all in `hardware/8bit-computer/`)

**`isa.py`** is the single source of truth: signals and micro-steps. Everything else
reads from it, so the EEPROM you burn holds exactly the microcode the simulator tested.

**`microcode.py`** builds the 2 KB image and prints the table:
```
0010  ADD   00     MI CO        RO II CE     MI IO        RO BI        AI EO FI
0111  JC    01     MI CO        RO II CE     IO J         -            -
```

**`sim8.py`** is a simulator that *doesn't know what instructions mean*. Each clock it
reads the control word **out of the EEPROM image** and obeys the signals: one bus
driver, then all "in"s latch on the rising edge. `--trace` shows every step:
```
-- fetch at pc=1
  T0 pc= 1 ir=00010100 a= 23 b=  0 bus=  1  MI CO
  T1 pc= 1 ir=00010100 a= 23 b=  0 bus= 37  RO II CE
  T2 pc= 2 ir=00100101 a= 23 b=  0 bus=  5  MI IO
  T3 pc= 2 ir=00100101 a= 23 b=  0 bus= 19  RO BI
  T4 pc= 2 ir=00100101 a= 23 b= 19 bus= 42  AI EO FI
```

**`asm8.py`**: programs are entered on DIP switches, so the assembler prints exactly
what to set, address by address:
```
addr  switches        hex  decoded
0000  0001 0100       14   LDA 4   (or data 20)
0001  0010 0101       25   ADD 5   (or data 37)
0010  1110 0000       e0   OUT 0   (or data 224)
0011  1111 0000       f0   HLT 0   (or data 240)
0100  0001 0111       17   LDA 7   (or data 23)
0101  0001 0011       13   LDA 3   (or data 19)
```
(The assembler can't know which bytes are code and which are data, so it shows
both readings. Bytes 4 and 5 are the data 23 and 19.)

**Tests** run every program on a freshly generated image, check no step has two
bus drivers, and check that no step latches an undriven bus.

**`eeprom-programmer/`**: the Arduino sketch burns any generated image. It uses the
28C16's **DATA polling** (bit 7 reads inverted until an internal write finishes)
instead of a fixed delay, skips bytes that are already right, and verifies.

### Bug the simulator caught
The first `fibonacci.asm` restarted after 144 without ever showing 233. The
overflow check was on `x + y` while `x` was being shown, so the last valid number
(`y` = 233) was skipped. The fix unrolls the loop twice so the values ping-pong
between two variables, and the first overflow jumps to "show y" instead of
restarting. It still fits in all 16 bytes.

---

## Practical build advice

- Build and test **one module at a time**, with the clock on single-step.
- A 0.1 µF decoupling capacitor across power at every chip; feed power to both
  ends of long breadboard rails. Most "random" faults are noise or voltage drop.
- Use current-limiting resistors on LEDs. LS outputs aren't made to drive LEDs directly.
- Unused LS inputs float (usually reading high); tie them to a defined level.
- When something misbehaves: single-step, read the bus and control LEDs, and
  compare with `sim8.py --trace` for the same program. The first step where they
  differ points at the faulty module.

## Check yourself

1. Why is the step counter clocked on the inverted clock?
2. `LDI 7` needs only one step after fetch. Why can't `LDA 7`?
3. How many EEPROM addresses does one instruction occupy, across both flags and both chips?
4. What does the display show for 0xFF in two's complement mode, and why?

<details><summary>Answers</summary>

1. Control signals then change on the falling edge, so they're settled by the rising edge when registers latch.
2. LDI's value is inside the instruction (IR low nibble → A). LDA needs the address into the MAR (one step), then RAM → A (a second step), because the bus carries one value per step.
3. 8 steps × 2 chips × 4 flag combinations = 64 bytes.
4. `-  1`: 0xFF = −1 in two's complement.
</details>
