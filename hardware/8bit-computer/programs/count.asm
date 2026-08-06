; Counts up by 3 forever: 0 3 6 ... 255 wraps to 2 5 8 ...
; (8-bit arithmetic wraps around at 256)
top:    out
        add step
        jmp top
step:   db 3
