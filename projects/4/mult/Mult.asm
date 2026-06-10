// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

// Pseudocode:
//   product = 0
//   count = R1
//   while (count > 0) { product = product + R0; count = count - 1 }
//   R2 = product
// R0 and R1 are never modified, only read.

    @R2
    M=0             // R2 = 0 (accumulate straight into the result)
    @R1
    D=M
    @count
    M=D             // count = R1   (count is a variable -> lives at RAM[16])

(LOOP)
    @count
    D=M
    @END
    D;JLE           // if count <= 0 we are done

    @R0
    D=M
    @R2
    M=D+M           // R2 = R2 + R0

    @count
    M=M-1           // count = count - 1
    @LOOP
    0;JMP

(END)
    @END
    0;JMP           // Hack has no "halt": spin forever on purpose
