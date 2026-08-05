#!/usr/bin/env python3
"""
Cycle-level simulator of the 8-bit breadboard computer.

    python3 sim8.py programs/fibonacci.asm            run, print the output register
    python3 sim8.py programs/multiply.asm --trace     show every micro-step

It does NOT know what "LDA" means. Each clock it reads the control word
out of build/microcode.bin - the same bytes that get burned into the
EEPROMs - and obeys the individual signals, just like the hardware does.
So if the simulator runs a program correctly, the EEPROM image is right.

One clock cycle, as on the breadboard:
  1. clock LOW : the step counter has advanced; the EEPROMs now output the
                 control word for (flags, opcode, step).
                 Whichever module has its "O" signal on drives the bus.
  2. clock HIGH (rising edge): every module with its "I" signal on latches
                 the bus at the same instant; the PC counts if CE; the flags
                 latch if FI.
"""
import argparse
from pathlib import Path

from isa import SIGNALS, BUS_DRIVERS, STEPS, describe
from microcode import address

HERE = Path(__file__).parent


class BusConflict(Exception):
    pass


class Computer:
    def __init__(self, ram: list[int], rom: bytes | None = None):
        self.rom = rom or (HERE / "build" / "microcode.bin").read_bytes()
        self.ram = (list(ram) + [0] * 16)[:16]
        self.a = self.b = self.ir = self.mar = self.pc = self.out = 0
        self.carry = self.zero = 0          # the flags register (74LS173)
        self.step = 0
        self.halted = False
        self.outputs: list[int] = []        # every value written to the display
        self.cycles = 0

    # The control EEPROMs: two look-ups, one per chip, glued into 16 bits.
    def control_word(self) -> int:
        flags = (self.zero << 1) | self.carry
        opcode = self.ir >> 4
        high = self.rom[address(flags, 0, opcode, self.step)]
        low = self.rom[address(flags, 1, opcode, self.step)]
        return (high << 8) | low

    def alu(self, subtract: bool):
        """74LS283 adders + 74LS86 XORs: A + B, or A + ~B + 1 for subtraction."""
        b = (~self.b & 0xFF) if subtract else self.b
        total = self.a + b + (1 if subtract else 0)
        result = total & 0xFF
        return result, total >> 8 & 1, int(result == 0)

    def clock(self, trace=False):
        word = self.control_word()
        on = {name for name, bit in SIGNALS.items() if word >> bit & 1}
        if "HLT" in on:
            self.halted = True
            return

        sum_, carry, zero = self.alu("SU" in on)

        # --- the bus: exactly one driver or none (pull-down resistors -> 0)
        drivers = [s for s in BUS_DRIVERS if s in on]
        if len(drivers) > 1:
            raise BusConflict(f"step {self.step}: {drivers} drive the bus together")
        bus = {
            "RO": lambda: self.ram[self.mar],
            "IO": lambda: self.ir & 0x0F,
            "AO": lambda: self.a,
            "EO": lambda: sum_,
            "CO": lambda: self.pc,
        }[drivers[0]]() if drivers else 0

        if trace:
            print(f"  T{self.step} pc={self.pc:2} ir={self.ir:08b} a={self.a:3} b={self.b:3} "
                  f"bus={bus:3}  {describe(word)}")

        # --- rising edge: everybody latches at once
        if "MI" in on: self.mar = bus & 0x0F
        if "RI" in on: self.ram[self.mar] = bus
        if "II" in on: self.ir = bus
        if "AI" in on: self.a = bus
        if "BI" in on: self.b = bus
        if "OI" in on:
            self.out = bus
            self.outputs.append(bus)
        if "FI" in on: self.carry, self.zero = carry, zero
        if "J" in on: self.pc = bus & 0x0F
        elif "CE" in on: self.pc = (self.pc + 1) & 0x0F

        # --- step counter: counts T0..T4 then resets (the '138 decodes T5 -> reset)
        self.step = (self.step + 1) % STEPS
        self.cycles += 1

    def run(self, max_cycles=100_000, max_outputs=None, trace=False):
        while not self.halted and self.cycles < max_cycles:
            if trace and self.step == 0:
                print(f"-- fetch at pc={self.pc}")
            self.clock(trace)
            if max_outputs and len(self.outputs) >= max_outputs:
                break
        return self.outputs


def main():
    from asm8 import assemble_file
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("program")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--max-outputs", type=int, default=40)
    args = p.parse_args()
    c = Computer(assemble_file(args.program))
    outputs = c.run(max_outputs=args.max_outputs, trace=args.trace)
    print("output:", " ".join(map(str, outputs)))
    print("halted" if c.halted else "still running", f"after {c.cycles} clock cycles")


if __name__ == "__main__":
    main()
