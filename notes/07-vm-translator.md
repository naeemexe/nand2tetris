# 07 — The VM translator (projects 7–8)

**Goal:** translate a stack-based virtual machine language into Hack assembly.
This is the middle layer that lets the compiler (note 08) ignore the details of
the Hack CPU. `projects/8/vm_translator.py`, built in two commits: project 7
(arithmetic + memory), then project 8 (branching + functions).

## 1. Why a stack machine?

Compilers love stacks: `a + b * c` becomes "push a, push b, push c, multiply,
add". No register allocation, no temporaries. Every operation takes its operands
off the top of the stack and pushes the result.

```
push constant 7      stack: 7
push constant 8      stack: 7 8
add                  stack: 15
```

## 2. The memory layout the translator maintains

```
RAM[0]  SP     → next free stack slot
RAM[1]  LCL    → current function's local variables
RAM[2]  ARG    → current function's arguments
RAM[3]  THIS   → current object's fields
RAM[4]  THAT   → current array
RAM[5–12]      temp segment
RAM[13–15]     scratch for the translator
RAM[16–255]    static variables
RAM[256– ]     the stack
```

## 3. Project 7: push, pop, arithmetic

Two building blocks used everywhere:

```
PUSH D:  @SP  A=M  M=D  @SP  M=M+1      // *SP = D; SP++
POP  D:  @SP  AM=M-1  D=M               // SP--; D = *SP
```

**Segments**, each mapped to a different address:
| segment | address of entry i | |
|---|---|---|
| constant | – (just the number) | `@i D=A` |
| local / argument / this / that | base pointer + i | `@i D=A @LCL A=D+M` |
| temp | 5 + i | `@R(5+i)` |
| pointer 0 / 1 | THIS / THAT themselves | |
| static | a symbol `File.i` | the assembler picks the RAM slot |

**pop to `local i`** has a catch: D is needed for the popped value *and* to compute
`LCL + i`. Solution: compute the address first, park it in R13, then pop, then
`@R13 A=M M=D`.

**Arithmetic**: binary ops pop y, then operate on x *in place* (no need to pop x
and push again):  `POP D, A=A-1, M=M+D`.

**Comparisons** (`eq gt lt`) need jumps and labels. Instead of pasting ~12
instructions with fresh labels at every use, they're emitted **once** as shared
routines at the end of the program. Each use site stores a return address in D
and jumps:

```
@RET.7  D=A  @$$EQ  0;JMP  (RET.7)
```

## 4. Project 8: branching

`label X`, `goto X`, `if-goto X` (pop; jump if not 0). Labels are scoped to the
current function by writing them as `Function$X`, so two functions can both
use `LOOP`.

## 5. Project 8: functions, the heart of it

`call f n` must save the caller's world, and `return` must restore it. The
**frame** pushed on the stack by `call`:

```
          ┌────────────┐
 ARG ───► │ arg 0      │  ← pushed by the caller before "call"
          │ ...        │
          │ arg n-1    │
          │ return addr│  ┐
          │ saved LCL  │  │
          │ saved ARG  │  │ the frame (5 words)
          │ saved THIS │  │
          │ saved THAT │  ┘
 LCL ───► │ local 0    │  ← zeroed by "function f k"
          │ ...        │
 SP  ───► │            │
          └────────────┘
```

**call f n**: push return address, LCL, ARG, THIS, THAT; `ARG = SP − 5 − n`;
`LCL = SP`; `goto f`; then `(return address)`.

**return**:
```
frame = LCL
ret   = *(frame − 5)      // save it FIRST: if n = 0, the next line overwrites it
*ARG  = pop()             // return value goes where arg 0 was
SP    = ARG + 1           // caller sees just the return value
THAT, THIS, ARG, LCL = *(frame−1), *(frame−2), *(frame−3), *(frame−4)
goto ret
```

The subtle line is saving `ret` before `*ARG = pop()`: with zero arguments ARG
points exactly at the return-address slot, so writing the result there would
destroy it.

**Bootstrap** (only for whole programs, i.e. folders with `Sys.vm`): `SP = 256; call Sys.init`.

## 6. The size problem, and shared call/return

Inline, every `call` is ~45 instructions and every `return` ~40. The Jack OS +
Pong has hundreds of calls, so that would blow past the 32K-word ROM. Like the
comparisons, `call` and `return` are shared routines: a call site just loads
nArgs (R13), the target (R14) and the return address (D), about 10 instructions.

Result: Pong + the full OS, through this repo's compiler → translator → assembler,
is **27,825 instructions** and runs on the CPU emulator.

## Check yourself

1. Translate `push local 2` by hand.
2. Why `A=A-1` (not another pop) in binary arithmetic?
3. What is `ARG` right after `call f 0`, relative to the return-address slot?

<details><summary>Answers</summary>

1. `@2 D=A @LCL A=D+M D=M @SP A=M M=D @SP M=M+1`.
2. x stays on the stack and gets overwritten with the result, which saves a pop and a push.
3. ARG = SP − 5 − 0 = the return-address slot itself. That's why `ret` must be saved before `*ARG = pop()`.
</details>
