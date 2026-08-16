# 08 — Jack, and the Jack compiler (projects 9–11)

**Goal:** write a program in Jack (Snake), then build the compiler that turns
Jack into VM code: tokenizer → parser → code generator.

## 1. Jack in one screen (project 9)

Java-like, deliberately simple: classes; `field`/`static`/`var`; `function`
(static), `method` (has `this`), `constructor`; statements `let do if while return`;
types `int char boolean` + class names; **no operator precedence** (strictly left
to right, so use parentheses).

**Snake** (`projects/9/Snake`), the design decisions:
- **Ring buffer body.** A move = add a head cell + remove the tail cell. Shifting
  an array would cost O(length); with a ring buffer both ends are O(1).
- **Occupancy grid.** "Did I bite myself?" is one array read instead of a walk
  over the body.
- **Free the tail before moving the head**, so moving into the cell your tail is
  just leaving is legal (it is in real Snake).
- **Randomness**: a 16-bit LCG (`seed = seed·25173 + 13849`), seeded by how many
  loop iterations pass on the title screen before you press a key.

## 2. Tokenizer (`projects/10/jack_tokenizer.py`)

Source text → a list of tokens of 5 kinds: keyword, symbol, integerConstant,
stringConstant, identifier. Implemented as **one regular expression** with a named
group per kind. Comments and whitespace are groups too; they're matched and
thrown away. Order matters: alternatives are tried left to right at each position.

## 3. Parser: recursive descent (`projects/10/jack_analyzer.py`)

The grammar, written as rules:

```
class          : 'class' name '{' classVarDec* subroutineDec* '}'
statements     : (let | if | while | do | return)*
expression     : term (op term)*
term           : int | string | keyword | var | var '[' expr ']' | call | '(' expr ')' | unaryOp term
```

**One method per rule.** Each method consumes exactly its rule's tokens and calls
the methods of the rules inside it. `compile_expression` calls `compile_term`,
which may call `compile_expression` again for `( … )`. The recursion in the code
mirrors the recursion in the grammar, so the XML output is a picture of the call stack.

Lookahead: almost always the current token decides which rule applies. The
exception is a term starting with an identifier, where you have to peek at the next
token: `[` → array, `(` or `.` → call, otherwise → plain variable.

Verified: every provided `.xml` / `T.xml` matches exactly.

## 4. Code generation (`projects/11/jack_compiler.py`)

Same parser, but instead of XML each rule emits VM code.

### Symbol table
Every name maps to *(type, kind, index)*, and the kind is the VM segment:

| kind | segment | scope |
|---|---|---|
| static | static | class |
| field | this | class |
| argument | argument | subroutine |
| var | local | subroutine |

So `let x = 5;` with `x` = var #2 becomes `push constant 5 / pop local 2`.

### Expressions: emit operands, then operator (postfix)
`x + y * 2` (left to right, no precedence!) →
```
push x / push y / add / push constant 2 / call Math.multiply 2
```

### The interesting translations
| Jack | VM | the idea |
|---|---|---|
| `if (c) {A} else {B}` | `c; not; if-goto ELSE; A; goto END; label ELSE; B; label END` | jumps around code |
| `while (c) {S}` | `label TOP; c; not; if-goto END; S; goto TOP; label END` | |
| `a[i]` (read) | `push a; push i; add; pop pointer 1; push that 0` | THAT points at the element |
| `let a[i] = e` | `push a; push i; add; e; pop temp 0; pop pointer 1; push temp 0; pop that 0` | `e` is computed **before** THAT is set, because `e` may contain another array access |
| `"hi"` | `push 2; call String.new 1; push 104; call String.appendChar 2; …` | appendChar returns the string, so it chains |
| `true` | `push constant 0; not` | −1 = all ones |
| constructor | `push nFields; call Memory.alloc 1; pop pointer 0` | allocate the object, point THIS at it |
| method | `push argument 0; pop pointer 0` | `this` is secretly argument 0 |
| `obj.m(x)` | `push obj; push x; call Class.m 2` | the object is the hidden first argument |
| `do f();` | `…; pop temp 0` | discard the return value |

### Verified
Each project 11 program was compiled twice (this compiler and the official one)
and run for 3 million steps in the VM emulator. The screen memory was identical
for Seven, ConvertToBin, Average, ComplexArrays, Square and Pong.

## Check yourself

1. Why does Jack have no operator precedence? What does `2 + 3 * 4` evaluate to?
2. Compile `let a[i] = b[j];` by hand. Where would it break if THAT were set first?
3. Why does a method call push the object before the arguments?

<details><summary>Answers</summary>

1. It keeps the compiler trivial. The answer is (2 + 3) · 4 = 20.
2. `push a, push i, add, push b, push j, add, pop pointer 1, push that 0, pop temp 0, pop pointer 1, push temp 0, pop that 0`. If THAT were set to a+i first, evaluating `b[j]` would overwrite THAT.
3. It becomes argument 0 of the callee, which is what `push argument 0; pop pointer 0` expects.
</details>
