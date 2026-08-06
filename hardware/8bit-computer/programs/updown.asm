; Counts 0 -> 255 by fives, then back down to 0, forever (no repeats at the ends).
; Shows both flags: carry ends the climb, zero ends the descent.
up:     out
        add step
        jc down         ; passed 255 (wrapped to 4, carry set) -> turn around
        jmp up
down:   sub step        ; undo the step that overflowed: back to 255 (already shown)
dloop:  sub step
        jz up           ; reached 0 -> climb again (up shows the 0)
        out
        jmp dloop
step:   db 5
