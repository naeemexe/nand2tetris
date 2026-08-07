"""
Run every example program on the simulator, which executes the real
EEPROM image (build/microcode.bin). Run with:  python3 -m pytest tests  (or plain python3 tests/test_programs.py)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import microcode                      # noqa: E402
from asm8 import assemble_file        # noqa: E402
from sim8 import Computer             # noqa: E402

ROM = microcode.build_image()          # always test the image as generated right now


def run(name, **kw):
    c = Computer(assemble_file(ROOT / "programs" / name), rom=ROM)
    return c, c.run(**kw)


def test_add():
    c, out = run("add.asm")
    assert out == [42] and c.halted


def test_add_sub_and_store():
    c, out = run("add_sub.asm")
    assert out == [35] and c.halted
    assert c.ram[9] == 35                # STA really wrote RAM ("result" is byte 9)


def test_count_wraps_at_256():
    _, out = run("count.asm", max_outputs=90)
    assert out[:4] == [0, 3, 6, 9]
    assert out[85:87] == [255, 2]       # 255 + 3 = 258 -> 2


def test_multiply():
    c, out = run("multiply.asm")
    assert out == [56] and c.halted


def test_fibonacci_restarts_after_233():
    _, out = run("fibonacci.asm", max_outputs=16)
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    assert out == fib + fib[:2]


def test_updown():
    _, out = run("updown.asm", max_outputs=110)
    up = list(range(0, 256, 5))
    down = list(range(250, 0, -5))
    assert out[:len(up) + len(down) + 2] == up + down + [0, 5]


def test_microcode_has_no_bus_conflicts():
    from isa import BUS_DRIVERS, SIGNALS, micro_steps
    for opcode in range(16):
        for flags in range(4):
            for word in micro_steps(opcode, flags):
                drivers = [s for s in BUS_DRIVERS if word >> SIGNALS[s] & 1]
                assert len(drivers) <= 1, (opcode, flags, drivers)


def test_image_layout():
    # LDA, step T2 = IO|MI: high chip byte has MI (bit 14 -> 0x40) + IO (bit 11 -> 0x08)
    addr_high = (0 << 8) | (0 << 7) | (0b0001 << 3) | 2
    assert ROM[addr_high] == 0x48
    # JC taken only in the carry copy of the microcode
    jc_t2 = lambda flags: (ROM[(flags << 8) | (0b0111 << 3) | 2] << 8) | ROM[(flags << 8) | (1 << 7) | (0b0111 << 3) | 2]
    assert jc_t2(0b00) == 0 and jc_t2(0b01) != 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
