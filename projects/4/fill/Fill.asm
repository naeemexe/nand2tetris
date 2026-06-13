// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

// Pseudocode:
//   forever:
//     color = (KBD != 0) ? -1 : 0      // -1 = 1111111111111111 = 16 black pixels
//     for (addr = SCREEN; addr < KBD; addr++) RAM[addr] = color
//
// The screen is 256 rows x 512 pixels = 8192 words, from SCREEN (16384)
// up to just below KBD (24576), so KBD conveniently doubles as the end marker.

(MAIN)
    @color
    M=0             // assume white
    @KBD
    D=M
    @PAINT
    D;JEQ           // no key -> keep white
    @color
    M=-1            // some key -> black

(PAINT)
    @SCREEN
    D=A
    @addr
    M=D             // addr = SCREEN

(PAINTLOOP)
    @addr
    D=M
    @KBD
    D=D-A
    @MAIN
    D;JGE           // addr >= KBD -> whole screen painted, poll keyboard again

    @color
    D=M
    @addr
    A=M             // jump to the address held in addr (pointer dereference)
    M=D             // RAM[addr] = color

    @addr
    M=M+1
    @PAINTLOOP
    0;JMP
