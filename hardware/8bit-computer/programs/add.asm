; First program: add two numbers from memory and show the result.
; 23 + 19 = 42 on the display, then halt.
        lda first       ; A = RAM[first]
        add second      ; A = A + RAM[second]
        out             ; display A
        hlt
first:  db 23
second: db 19
