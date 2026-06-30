#!/usr/bin/env python3
"""
VM translator, stage 1 (Nand2Tetris project 7: stack arithmetic + memory access).

    python3 vm_translator.py Prog.vm      ->  Prog.asm

Translates the stack-based VM language into Hack assembly.

Memory layout the generated code relies on:

    RAM[0]  SP    -> next free stack slot
    RAM[1]  LCL   -> base of current function's locals
    RAM[2]  ARG   -> base of current function's arguments
    RAM[3]  THIS  -> base of 'this' segment (object fields)
    RAM[4]  THAT  -> base of 'that' segment (array elements)
    RAM[5-12]     temp segment
    RAM[13-15]    scratch registers for the translator itself
    RAM[16-255]   static variables (assembler gives them out as @File.i)
    RAM[256-]     the stack

Design choice (my own, not required by the course): the three comparisons
(eq/gt/lt) need jumps, so instead of pasting ~12 instructions with fresh
labels at every use, each is emitted ONCE as a shared subroutine at the end
of the program. A use site stores its return address in D and jumps there.
"""
import sys
from pathlib import Path

SEGMENT_POINTER = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
TEMP_BASE = 5
ARITH_BINARY = {"add": "M=D+M", "sub": "M=M-D", "and": "M=D&M", "or": "M=D|M"}
ARITH_UNARY = {"neg": "M=-M", "not": "M=!M"}
COMPARE = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}

# Small asm building blocks (each a list of lines) ------------------------
PUSH_D = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]          # *SP = D; SP++
POP_D = ["@SP", "AM=M-1", "D=M"]                        # SP--; D = *SP


class Translator:
    def __init__(self):
        self.out: list[str] = []
        self.file = ""          # current .vm file name (for statics)
        self.counter = 0        # makes return labels unique

    def emit(self, *lines):
        self.out.extend(lines)

    def unique(self, prefix):
        self.counter += 1
        return f"{prefix}.{self.counter}"

    # ---- push / pop -----------------------------------------------------
    def address_of(self, segment, index):
        """Lines that leave the target RAM address in A (for non-constant segments)."""
        if segment in SEGMENT_POINTER:
            # base pointer + index; the common index 0 skips the addition.
            if index == 0:
                return [f"@{SEGMENT_POINTER[segment]}", "A=M"]
            return [f"@{index}", "D=A", f"@{SEGMENT_POINTER[segment]}", "A=D+M"]
        if segment == "temp":
            if not 0 <= index <= 7:
                raise ValueError("temp index must be 0..7")
            return [f"@R{TEMP_BASE + index}"]
        if segment == "pointer":
            if index not in (0, 1):
                raise ValueError("pointer index must be 0 or 1")
            return ["@THIS" if index == 0 else "@THAT"]
        if segment == "static":
            return [f"@{self.file}.{index}"]
        raise ValueError(f"unknown segment '{segment}'")

    def write_push(self, segment, index):
        if segment == "constant":
            if index in (0, 1):                 # tiny shortcut: no A-load needed
                self.emit("@SP", "A=M", f"M={index}", "@SP", "M=M+1")
                return
            self.emit(f"@{index}", "D=A", *PUSH_D)
        else:
            self.emit(*self.address_of(segment, index), "D=M", *PUSH_D)

    def write_pop(self, segment, index):
        if segment == "constant":
            raise ValueError("can't pop into constant")
        if segment in SEGMENT_POINTER and index != 0:
            # Address needs D for the addition, but so does the popped value.
            # Park the address in R13 first.
            self.emit(*self.address_of(segment, index), "D=A", "@R13", "M=D",
                      *POP_D, "@R13", "A=M", "M=D")
        else:
            self.emit(*POP_D, *self.address_of(segment, index), "M=D")

    # ---- arithmetic / logic ---------------------------------------------
    def write_arithmetic(self, op):
        if op in ARITH_BINARY:
            # y = pop; x = top (left in place); x = x op y
            self.emit(*POP_D, "A=A-1", ARITH_BINARY[op])
        elif op in ARITH_UNARY:
            self.emit("@SP", "A=M-1", ARITH_UNARY[op])
        elif op in COMPARE:
            ret = self.unique("$cmp.ret")
            self.emit(f"@{ret}", "D=A", f"@$${op.upper()}", "0;JMP", f"({ret})")
        else:
            raise ValueError(f"unknown command '{op}'")

    # ---- shared subroutines ---------------------------------------------
    def write_runtime(self):
        self.emit("// ---- end of program: park here so we never fall into the runtime",
                  "($$END)", "@$$END", "0;JMP")

        # Comparisons. Entered with D = return address.
        for op, jump in COMPARE.items():
            name = f"$${op.upper()}"
            self.emit(f"// {name}: x = (x {op} y) ? -1 : 0",
                      f"({name})", "@R15", "M=D",
                      *POP_D, "A=A-1", "D=M-D",            # D = x - y, A -> x
                      "M=0",                                # assume false
                      f"@{name}.TRUE", f"D;{jump}",
                      "@R15", "A=M", "0;JMP",
                      f"({name}.TRUE)", "@SP", "A=M-1", "M=-1",
                      "@R15", "A=M", "0;JMP")

    # ---- driver ---------------------------------------------------------
    def translate_file(self, path: Path):
        self.file = path.stem
        for number, raw in enumerate(path.read_text().splitlines(), start=1):
            line = raw.split("//", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            cmd = parts[0]
            self.emit(f"// {line}")
            try:
                if cmd == "push":
                    self.write_push(parts[1], int(parts[2]))
                elif cmd == "pop":
                    self.write_pop(parts[1], int(parts[2]))
                else:
                    self.write_arithmetic(cmd)
            except (ValueError, IndexError) as err:
                raise SystemExit(f"{path}:{number}: {err}: '{line}'")


def translate(target: Path) -> Path:
    t = Translator()
    out = target.with_suffix(".asm")
    t.translate_file(target)
    t.write_runtime()
    out.write_text("\n".join(t.out) + "\n")
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: vm_translator.py File.vm")
    out = translate(Path(sys.argv[1]).resolve())
    print(f"-> {out}")


if __name__ == "__main__":
    main()
