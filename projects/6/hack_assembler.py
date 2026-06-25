#!/usr/bin/env python3
"""
Hack assembler (Nand2Tetris project 6).

    python3 hack_assembler.py Prog.asm        ->  writes Prog.hack next to it

Translates Hack assembly into 16-bit binary machine code, one instruction
per line, written as text '0'/'1' characters (the format the CPU emulator
and the ROM32K chip load).

The job is split into the same three pieces as the book:

  Parser       - strips comments/whitespace, classifies each line
  Code         - lookup tables: mnemonic -> bits
  SymbolTable  - labels  (LOOP)  and variables  @i  -> addresses

and the classic TWO passes:

  pass 1: walk the program, count real instructions, and record the ROM
          address of every (LABEL). Labels can be used before they are
          declared, which is why we need a full pass first.
  pass 2: translate every instruction. Any @symbol that is still unknown
          after pass 1 must be a variable, so give it the next free RAM
          address starting at 16.
"""
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Code: bit patterns for the three fields of a C-instruction
#   111 a c1c2c3c4c5c6 d1d2d3 j1j2j3
# The 'a' bit is folded into the comp table (7 bits): computations that use
# M instead of A have a=1.
# --------------------------------------------------------------------------
COMP = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "M":   "1110000",
    "!D":  "0001101", "!A":  "0110001", "!M":  "1110001",
    "-D":  "0001111", "-A":  "0110011", "-M":  "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101",
}

JUMP = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}


def dest_bits(dest: str) -> str:
    """d1 d2 d3 = A, D, M. Order inside the mnemonic doesn't matter (MD == DM)."""
    return "".join("1" if reg in dest else "0" for reg in "ADM")


def comp_bits(comp: str) -> str:
    if comp in COMP:
        return COMP[comp]
    # Accept commutative spellings like A+D, M+D, A&D, M|D.
    for op in "+&|":
        if op in comp:
            left, right = comp.split(op)
            swapped = right + op + left
            if swapped in COMP:
                return COMP[swapped]
    raise SyntaxError(f"unknown computation '{comp}'")


# --------------------------------------------------------------------------
# SymbolTable
# --------------------------------------------------------------------------
def predefined_symbols() -> dict:
    table = {f"R{i}": i for i in range(16)}
    table.update({
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 0x4000, "KBD": 0x6000,
    })
    return table


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------
def clean_lines(source: str):
    """Yield (line_number, instruction) with comments and all spaces removed."""
    for number, raw in enumerate(source.splitlines(), start=1):
        line = raw.split("//", 1)[0]
        line = "".join(line.split())        # Hack has no meaningful spaces
        if line:
            yield number, line


def split_c(instr: str):
    """'dest=comp;jump' -> (dest, comp, jump); dest and jump are optional."""
    dest, _, rest = instr.rpartition("=")  # no '=' -> dest is ''
    comp, _, jump = rest.partition(";")
    return dest, comp, jump


# --------------------------------------------------------------------------
# The assembler proper
# --------------------------------------------------------------------------
def assemble(source: str) -> list[str]:
    symbols = predefined_symbols()
    lines = list(clean_lines(source))

    # ---- pass 1: labels -> ROM addresses
    rom_address = 0
    for number, instr in lines:
        if instr.startswith("("):
            if not instr.endswith(")"):
                raise SyntaxError(f"line {number}: bad label '{instr}'")
            symbols[instr[1:-1]] = rom_address   # points at the NEXT instruction
        else:
            rom_address += 1

    # ---- pass 2: translate
    next_variable = 16
    output = []
    for number, instr in lines:
        if instr.startswith("("):
            continue                              # labels generate no code

        try:
            if instr.startswith("@"):             # A-instruction: 0vvvvvvvvvvvvvvv
                value = instr[1:]
                if value.isdigit():
                    address = int(value)
                else:
                    if value not in symbols:      # first sighting -> new variable
                        symbols[value] = next_variable
                        next_variable += 1
                    address = symbols[value]
                if not 0 <= address < 2 ** 15:
                    raise SyntaxError(f"constant {address} doesn't fit in 15 bits")
                output.append(f"{address:016b}")

            else:                                 # C-instruction: 111a cccc ccdd djjj
                dest, comp, jump = split_c(instr)
                if jump not in JUMP:
                    raise SyntaxError(f"unknown jump '{jump}'")
                if any(c not in "ADM" for c in dest):
                    raise SyntaxError(f"unknown destination '{dest}'")
                output.append("111" + comp_bits(comp) + dest_bits(dest) + JUMP[jump])
        except SyntaxError as err:
            raise SyntaxError(f"line {number}: {err}") from None

    return output


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: hack_assembler.py Prog.asm")
    src = Path(sys.argv[1])
    out = src.with_suffix(".hack")
    out.write_text("\n".join(assemble(src.read_text())) + "\n")
    print(f"{src} -> {out}")


if __name__ == "__main__":
    main()
