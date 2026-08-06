; Exercises LDI, ADD, SUB and STA: computes (9 + 30 - 4) and stores it.
        ldi 9           ; A = 9 (immediate: only 0..15 fits in the operand)
        add thirty      ; A = 39
        sub four        ; A = 35
        sta result      ; RAM[result] = 35
        lda result      ; read it back, to prove the store worked
        out
        hlt
thirty: db 30
four:   db 4
result: db 0
