#!/usr/bin/env python3
"""
Assembler for the 8-bit breadboard computer.

    python3 asm8.py programs/multiply.asm

Prints the 16 RAM bytes as DIP-switch settings, which is how a program
actually gets into the breadboard computer: in program mode you set the
4 address switches and the 8 data switches, then press the write button,
16 times.

Syntax:
    label:  MNEMONIC operand    ; comment
            db 42               ; a raw data byte
Operands are numbers (decimal, 0x.., 0b..) or labels. Every instruction is
one byte: opcode in the high nibble, operand (address or immediate, 0..15)
in the low nibble.
"""
import sys

from isa import INSTRUCTIONS, MNEMONICS


def parse_number(text: str, labels: dict) -> int:
    if text in labels:
        return labels[text]
    return int(text, 0)


def assemble(source: str) -> list[int]:
    lines = []
    labels = {}
    # pass 1: labels -> addresses
    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if ":" in line:
            label, line = (part.strip() for part in line.split(":", 1))
            labels[label] = len(lines)
        if line:
            lines.append((number, line.split()))
    if len(lines) > 16:
        raise SystemExit(f"program is {len(lines)} bytes; the RAM only has 16")

    # pass 2: encode
    ram = []
    for number, parts in lines:
        op = parts[0].upper()
        try:
            if op == "DB":
                value = parse_number(parts[1], labels)
                if not 0 <= value <= 255:
                    raise ValueError("db value must be 0..255")
                ram.append(value)
                continue
            if op not in MNEMONICS:
                raise ValueError(f"unknown instruction {op}")
            opcode = MNEMONICS[op]
            takes_operand = INSTRUCTIONS[opcode][1]
            operand = 0
            if takes_operand:
                operand = parse_number(parts[1], labels)
                if not 0 <= operand <= 15:
                    raise ValueError("operand must fit in 4 bits (0..15)")
            elif len(parts) > 1:
                raise ValueError(f"{op} takes no operand")
            ram.append(opcode << 4 | operand)
        except (ValueError, IndexError) as err:
            raise SystemExit(f"line {number}: {err}")
    return ram + [0] * (16 - len(ram))


def assemble_file(path) -> list[int]:
    with open(path) as f:
        return assemble(f.read())


def listing(ram: list[int]) -> str:
    names = {op: name for name, op in MNEMONICS.items()}
    out = ["addr  switches        hex  decoded"]
    for addr, byte in enumerate(ram):
        op = names.get(byte >> 4, "?")
        out.append(f"{addr:04b}  {byte >> 4:04b} {byte & 15:04b}       {byte:02x}   "
                   f"{op} {byte & 15:<3} (or data {byte})")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: asm8.py program.asm")
    print(listing(assemble_file(sys.argv[1])))
