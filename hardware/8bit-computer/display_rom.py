#!/usr/bin/env python3
"""
Generate the output-display EEPROM image (28C16, 2 KB).

    python3 display_rom.py      ->  build/display.bin, ../eeprom-programmer/eeprom_programmer/display.h

The output register holds one byte, but four 7-segment digits need to
show it in decimal. Doing binary -> decimal in logic gates is painful;
an EEPROM does it as a lookup table instead.

The four digits share their segment wires and take turns being lit
(multiplexing): a 555 clocks a 2-bit counter (74LS107), the counter picks
the digit through a 74LS139 decoder AND tells the EEPROM which digit is
being shown. Fast enough and your eye sees all four at once.

EEPROM address lines:
    A10            A9 A8                     A7..A0
    mode           digit being lit           the value from the output register
    0=unsigned     00 ones, 01 tens,
    1=signed       10 hundreds, 11 sign

Data lines = segments. Each digit is drawn from segments a..g:

         a
       f   b
         g
       e   c
         d

SEGMENT_BITS maps each segment to the EEPROM data bit wired to it. With
this wiring '0' (a b c d e f lit, g off) is 0b0111_1110 = 0x7E.
"""
from pathlib import Path

from microcode import c_header

SEGMENT_BITS = {"a": 6, "b": 5, "c": 4, "d": 3, "e": 2, "f": 1, "g": 0}   # D7 = decimal point, unused

DIGIT_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g", " ": "",
}


def pattern(char: str) -> int:
    return sum(1 << SEGMENT_BITS[s] for s in DIGIT_SEGMENTS[char])


def digits_for(value: int, signed: bool) -> str:
    """4 characters, [sign, hundreds, tens, ones], e.g. ' 042' or '-128'."""
    if signed and value >= 128:
        value -= 256                    # two's complement: 0x80..0xFF are -128..-1
    text = f"{abs(value):3d}".replace(" ", "0")
    sign = "-" if value < 0 else " "
    # blank the leading zeros, but always keep the ones digit
    hundreds = text[0] if text[0] != "0" else " "
    tens = text[1] if (text[0] != "0" or text[1] != "0") else " "
    return sign + hundreds + tens + text[2]


def build_image() -> bytes:
    image = bytearray(2048)
    for signed in (0, 1):
        for value in range(256):
            sign, hundreds, tens, ones = digits_for(value, bool(signed))
            for digit, char in enumerate((ones, tens, hundreds, sign)):
                image[(signed << 10) | (digit << 8) | value] = pattern(char)
    return bytes(image)


def main():
    here = Path(__file__).parent
    image = build_image()
    (here / "build").mkdir(exist_ok=True)
    (here / "build" / "display.bin").write_bytes(image)
    (here.parent / "eeprom-programmer" / "eeprom_programmer" / "display.h").write_text(c_header(image, "display"))
    print("value  unsigned  signed")
    for v in (0, 7, 42, 127, 128, 200, 255):
        print(f"{v:5}   '{digits_for(v, False)}'   '{digits_for(v, True)}'")
    print("wrote build/display.bin and ../eeprom-programmer/eeprom_programmer/display.h")


if __name__ == "__main__":
    main()
