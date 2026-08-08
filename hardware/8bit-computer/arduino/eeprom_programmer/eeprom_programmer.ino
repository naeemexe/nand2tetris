/*
 * 28C16 EEPROM programmer for an Arduino Nano/Uno.
 *
 * The image to burn is NOT computed here. It comes from a header generated
 * by the Python scripts (microcode.py / display_rom.py), which are the same
 * scripts the simulator tests - so what you burn is what you tested.
 *
 *   1. python3 microcode.py      (or display_rom.py)
 *   2. pick the image below, upload, open the Serial Monitor at 115200
 *
 * Wiring
 *   Address: two 74HC595 shift registers in a chain (11 address lines needed,
 *            16 available). The very last output (bit 15) drives the
 *            EEPROM's /OE pin, so reading/writing is controlled from here too.
 *       pin 2 -> SER (data)   pin 3 -> SRCLK   pin 4 -> RCLK (latch)
 *   Data:    pins 5..12 -> EEPROM I/O0..I/O7
 *   Write:   pin 13 -> EEPROM /WE  (active low; idle HIGH)
 *   /CE of the EEPROM tied to GND.
 */

#define BURN_MICROCODE 1      // 1 = control logic microcode, 0 = 7-segment display decoder

#if BURN_MICROCODE
#include "microcode.h"
#else
#include "display.h"
#endif

const int SHIFT_DATA = 2;
const int SHIFT_CLK = 3;
const int SHIFT_LATCH = 4;
const int DATA_FIRST = 5;     // D5..D12 = I/O0..I/O7
const int WRITE_EN = 13;

// Put the address on A0..A10 and decide whether the EEPROM drives the data pins.
void setAddress(unsigned int address, bool outputEnable) {
  byte high = (address >> 8) & 0x07;
  if (!outputEnable) high |= 0x80;          // bit 15 -> /OE, high = outputs off
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, high);
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, address & 0xFF);
  digitalWrite(SHIFT_LATCH, LOW);           // copy the shifted bits to the outputs at once
  digitalWrite(SHIFT_LATCH, HIGH);
  digitalWrite(SHIFT_LATCH, LOW);
}

void dataPinsMode(int mode) {
  for (int i = 0; i < 8; i++) pinMode(DATA_FIRST + i, mode);
}

byte readData() {
  byte value = 0;
  for (int i = 7; i >= 0; i--) value = (value << 1) | digitalRead(DATA_FIRST + i);
  return value;
}

byte readEEPROM(unsigned int address) {
  dataPinsMode(INPUT);                      // never let both sides drive the pins
  setAddress(address, true);
  delayMicroseconds(1);
  return readData();
}

// Returns false if the chip never finished the write.
bool writeEEPROM(unsigned int address, byte value) {
  setAddress(address, false);               // EEPROM outputs off BEFORE we drive the pins
  dataPinsMode(OUTPUT);
  for (int i = 0; i < 8; i++) digitalWrite(DATA_FIRST + i, (value >> i) & 1);
  digitalWrite(WRITE_EN, LOW);              // /WE pulse latches address + data
  delayMicroseconds(1);
  digitalWrite(WRITE_EN, HIGH);

  // DATA polling: while the internal write is still going, reading the same
  // address returns the COMPLEMENT of bit 7. When bit 7 reads back true, it's done.
  // Faster and safer than guessing a fixed delay.
  unsigned long start = millis();
  while ((readEEPROM(address) & 0x80) != (value & 0x80)) {
    if (millis() - start > 20) return false;
  }
  return true;
}

void hexdump(unsigned int length) {
  char line[80];
  for (unsigned int base = 0; base < length; base += 16) {
    byte d[16];
    for (int i = 0; i < 16; i++) d[i] = readEEPROM(base + i);
    snprintf(line, sizeof(line), "%03x:  %02x %02x %02x %02x %02x %02x %02x %02x   %02x %02x %02x %02x %02x %02x %02x %02x",
            base, d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7],
            d[8], d[9], d[10], d[11], d[12], d[13], d[14], d[15]);
    Serial.println(line);
  }
}

void setup() {
  pinMode(SHIFT_DATA, OUTPUT);
  pinMode(SHIFT_CLK, OUTPUT);
  pinMode(SHIFT_LATCH, OUTPUT);
  digitalWrite(WRITE_EN, HIGH);             // set level before enabling the pin: no stray write
  pinMode(WRITE_EN, OUTPUT);
  Serial.begin(115200);

  Serial.print("Burning image '");
  Serial.print(IMAGE_NAME);
  Serial.print("' (");
  Serial.print(IMAGE_SIZE);
  Serial.println(" bytes)");

  unsigned int timeouts = 0;
  for (unsigned int address = 0; address < IMAGE_SIZE; address++) {
    byte value = pgm_read_byte(IMAGE + address);
    if (readEEPROM(address) == value) continue;   // already right: skip (saves write cycles)
    if (!writeEEPROM(address, value)) timeouts++;
    if (address % 128 == 0) Serial.print('.');
  }
  Serial.println();

  // Verify everything we meant to write.
  unsigned int errors = 0;
  for (unsigned int address = 0; address < IMAGE_SIZE; address++) {
    if (readEEPROM(address) != pgm_read_byte(IMAGE + address)) {
      if (errors < 10) {
        Serial.print("mismatch at 0x");
        Serial.println(address, HEX);
      }
      errors++;
    }
  }
  Serial.print("write timeouts: ");
  Serial.print(timeouts);
  Serial.print("   verify errors: ");
  Serial.println(errors);
  Serial.println(errors == 0 ? "OK" : "FAILED - check wiring and try again");

  Serial.println("first 256 bytes:");
  hexdump(256);
}

void loop() {}
