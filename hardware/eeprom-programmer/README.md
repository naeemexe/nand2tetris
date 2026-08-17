# EEPROM programmer (Arduino)

Burns the images generated in this repo into 28C16 / 28C256 EEPROMs.

| `IMAGE_CHOICE` | header | made by | chip |
|---|---|---|---|
| 1 | `microcode.h` | `../8bit-computer/microcode.py` | 28C16 (both control EEPROMs) |
| 2 | `display.h` | `../8bit-computer/display_rom.py` | 28C16 (output display) |
| 3 | `vga_image.h` | `../vga-card/image_to_rom.py` | 28C256 (picture) |

Circuit: two 74HC595 shift registers make 16 outputs from 3 Arduino pins
(A0–A14 + the EEPROM's `/OE`), pins 5–12 are the data bus, pin 13 is `/WE`.
Details in the comment at the top of the sketch.

Writes finish via **DATA polling** (the chip reads back an inverted bit 7 until
the internal write completes) rather than a fixed delay. Unchanged bytes are
skipped, and everything is verified at the end.
