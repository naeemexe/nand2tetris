# 09 — The operating system (project 12)

**Goal:** write the Jack OS in Jack: the library every program relies on for
memory, math, strings, graphics, text and keyboard input. Each class is its own
commit, in dependency order.

## 1. Math: arithmetic without hardware support

The Hack ALU can add but not multiply or divide.

**multiply**: grade-school multiplication in binary. For each 1-bit `i` of `y`,
add `x` shifted left `i` times:

```
sum = 0; shiftedX = x
for i in 0..15:
    if bit(y, i): sum += shiftedX
    shiftedX += shiftedX            // doubling = shift left
```
16 iterations regardless of size: O(n) in the number of bits. Negative numbers
just work, thanks to two's complement mod 2¹⁶.

**divide** (positive x, y): if `y > x`, the answer is 0. Otherwise
`q = divide(x, 2y)`, and the answer is `2q` or `2q + 1` depending on whether
`x − 2qy < y`. The `2qy` would need a multiplication, but each recursion level can
hand `q·y` up to its caller in a static variable, which keeps it to additions only.
If `y + y` goes negative it overflowed, which certainly means it's bigger than x.

**sqrt**: the answer fits in 8 bits. Try setting each bit from the top down and
keep it if `(y + 2^j)² ≤ x` (and the square didn't overflow to negative).

## 2. Memory: a heap allocator

Heap = RAM 2048–16383. Every block has a 1-word header holding its size:

```
block[0] = size          ← header (allocator's bookkeeping)
block[1] = next free     ← only while the block is free
caller gets block + 1
```

- **Free list sorted by address.** **alloc**: first fit. If the free block is big
  enough to split, carve the new block off its *end*, so the free block keeps its
  place in the list (no pointer updates). Otherwise hand over the whole block.
- **deAlloc**: insert in address order and **merge with neighbours that touch**.
  Without merging, the heap shatters into small pieces until big allocations
  fail even though plenty of total memory is free (*fragmentation*).
- `Memory.peek/poke` use a trick: `let ram = 0;` makes an `Array` whose base is
  address 0, so `ram[i]` *is* `RAM[i]`.

## 3. String, Array

`Array.new(n)` is just `Memory.alloc(n)`. A String is a char array + length.
`setInt` builds the digits on the **negative** value: −32768 has no positive
16-bit twin, but every positive number has a negative one.

## 4. Screen: pixels in words

Pixel (x, y) is bit `x % 16` of word `16384 + 32·y + x/16`. Setting one pixel
means read-modify-write: `word | mask` (black) or `word & ~mask` (white).

- **Horizontal runs** (used by rectangles and circles) fill whole words at once,
  with masks only on the two partial words at the ends. That's about 16× fewer
  memory writes than pixel by pixel.
- **Lines** use Bresenham's algorithm: an error term tracks how far the drawn
  pixels are from the true line; each step moves in x, y or both. Additions only.
  *Bug found while testing:* the first version could only step in x **or** y,
  which made diagonals 2 pixels thick. Comparing screens with the official OS
  showed it, and allowing diagonal steps fixed it.
- **Circles**: for each row `dy` from −r to r, draw a chord of half-width
  `√(r² − dy²)` (Pythagoras). `r ≤ 181` keeps `r²` under 32767.

## 5. Output: text

64 × 23 grid of 8×11-pixel cells, using a 2D font from `initMap`. Two
characters share each 16-bit screen word: even column = low byte, odd = high
byte. Drawing a character = for each of its 11 rows, `word = (word & keepMask) | glyphRow`.

*Matching detail found while testing:* the official OS draws each character one
pixel row lower, putting the spacing row above the glyph instead of below. Both
satisfy the spec; this OS matches the official one so screens can be compared
pixel for pixel. OutputTest and StringTest are now identical.

## 6. Keyboard, Sys

- `readChar` waits for a key **down** and then **up**; otherwise one long press
  would be read hundreds of times.
- `Sys.init` brings everything up in dependency order: Memory first, since
  everyone allocates, then Math, Screen, Output, Keyboard, then `Main.main`.

## How it was tested

The official test programs, compiled with this repo's compiler, running on this
OS (all 8 classes, no official ones mixed in):
- ArrayTest, MathTest, MemoryTest, MemoryDiag: pass their `.cmp` files
  (with more steps allowed, because an OS written in Jack runs as VM code, much
  slower than the emulator's built-in native OS)
- OutputTest, StringTest: screen identical to the official OS
- ScreenTest: identical except the top 6 rows of one circle; the official OS uses a
  different circle algorithm, while this one follows the book's chord formula exactly
- End-to-end: Pong + this OS → this translator → this assembler runs on the CPU emulator

## Check yourself

1. Why does alloc carve from the end of a free block rather than the start?
2. Trace `Math.divide(13, 4)`.
3. Why is the font's 'A' row data `12, 30, 51, 51, 63, 51, …`? Draw it.

<details><summary>Answers</summary>

1. Carving the start would move the free block's header, so the previous block's `next` pointer would need updating. Carving the end leaves the header where it is.
2. divide(13,4) → divide(13,8) → divide(13,16) = 0. Back at y=8: 13 − 0 ≥ 8, so 2·0+1 = 1. At y=4: 13 − 8 = 5 ≥ 4, so 2·1+1 = 3. ✔
3. In binary (bit 0 = leftmost pixel): `001100`, `011110`, `110011`, `110011`, `111111`, `110011`… That's an A.
</details>
