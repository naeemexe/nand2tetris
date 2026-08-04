"""
The 8-bit breadboard computer's control signals and instruction set.

This file is the SINGLE SOURCE OF TRUTH. The EEPROM image generator, the
assembler and the simulator all import from here, so the microcode that
gets burned into the chips is exactly the microcode the simulator tested.

Control word: 16 signals, one bit each. The two control EEPROMs each drive
8 of them; EEPROM "high" holds bits 15..8, EEPROM "low" holds bits 7..0.
The order below matches how the outputs are wired to the modules.
"""

# ---- control signals (bit positions in the 16-bit control word) ---------
# O = puts something ON the bus, I = takes it IN from the bus
HLT = 1 << 15   # halt: stop the clock
MI  = 1 << 14   # memory address register in  (low 4 bits of bus)
RI  = 1 << 13   # RAM in   (write bus into RAM[MAR])
RO  = 1 << 12   # RAM out
IO  = 1 << 11   # instruction register out (only its low 4 bits = the operand)
II  = 1 << 10   # instruction register in
AI  = 1 << 9    # A register in
AO  = 1 << 8    # A register out
EO  = 1 << 7    # ALU (sum) out  - "E" for the Greek sigma on the schematic
SU  = 1 << 6    # subtract: ALU computes A - B instead of A + B
BI  = 1 << 5    # B register in
OI  = 1 << 4    # output register in
CE  = 1 << 3    # counter enable: program counter += 1
CO  = 1 << 2    # counter out
J   = 1 << 1    # jump: load the program counter from the bus
FI  = 1 << 0    # flags in: latch carry & zero from the ALU

SIGNALS = {name: globals()[name].bit_length() - 1 for name in
           ("HLT", "MI", "RI", "RO", "IO", "II", "AI", "AO",
            "EO", "SU", "BI", "OI", "CE", "CO", "J", "FI")}

# Signals that drive the bus. Two at once would short the outputs together.
BUS_DRIVERS = ("RO", "IO", "AO", "EO", "CO")

# ---- micro-steps -------------------------------------------------------
STEPS = 5            # T0..T4; the step counter resets after T4 (74LS138 output 5)

# Every instruction starts with the same two steps:
#   T0: CO|MI      - put the PC on the bus and load it into the MAR
#   T1: RO|II|CE   - RAM[MAR] -> instruction register, and PC++
FETCH = [CO | MI, RO | II | CE]

# ---- instruction set ---------------------------------------------------
# opcode: (mnemonic, takes_operand, micro-steps T2.. ) - the fetch is added automatically.
# Steps left out are empty (do nothing) until the counter wraps.
INSTRUCTIONS = {
    0b0000: ("NOP", False, []),
    0b0001: ("LDA", True,  [IO | MI, RO | AI]),               # A = RAM[addr]
    0b0010: ("ADD", True,  [IO | MI, RO | BI, EO | AI | FI]), # A = A + RAM[addr]
    0b0011: ("SUB", True,  [IO | MI, RO | BI, EO | AI | SU | FI]),  # A = A - RAM[addr]
    0b0100: ("STA", True,  [IO | MI, AO | RI]),               # RAM[addr] = A
    0b0101: ("LDI", True,  [IO | AI]),                        # A = 4-bit immediate
    0b0110: ("JMP", True,  [IO | J]),                         # PC = addr
    0b0111: ("JC",  True,  None),                             # PC = addr if carry  (flag-dependent)
    0b1000: ("JZ",  True,  None),                             # PC = addr if zero   (flag-dependent)
    0b1110: ("OUT", False, [AO | OI]),                        # display A
    0b1111: ("HLT", False, [HLT]),                            # stop
}
MNEMONICS = {name: op for op, (name, _, _) in INSTRUCTIONS.items()}

# The flags register feeds two extra address lines of the control EEPROMs,
# so the microcode can be different depending on the flags. That's all a
# conditional jump is: the same opcode has a jump step in the "flag set"
# copy of the microcode and nothing in the "flag clear" copy.
FLAG_CARRY = 0b01
FLAG_ZERO = 0b10


def micro_steps(opcode: int, flags: int) -> list[int]:
    """The full T0..T4 control words for one instruction under given flags."""
    name, _, steps = INSTRUCTIONS.get(opcode, ("NOP", False, []))
    if name == "JC":
        steps = [IO | J] if flags & FLAG_CARRY else []
    elif name == "JZ":
        steps = [IO | J] if flags & FLAG_ZERO else []
    words = FETCH + steps
    assert len(words) <= STEPS, f"{name} has too many steps"
    return words + [0] * (STEPS - len(words))


def describe(word: int) -> str:
    """'CO MI' style text for a control word (for traces and docs)."""
    return " ".join(n for n, b in sorted(SIGNALS.items(), key=lambda kv: -kv[1]) if word >> b & 1) or "-"
