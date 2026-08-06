; Fibonacci: 0 1 1 2 3 5 8 13 21 34 55 89 144 233, then starts over.
; Uses all 16 bytes of RAM.
;
; The loop is unrolled twice so the numbers can ping-pong between y and z
; without a third "swap" variable:   A=x  ->  z = x+y  ->  y = y+z  -> A=z
;
; Overflow: the carry flag goes up when a sum passes 255. The FIRST sum
; to overflow is computed while y (=233) still hasn't been shown, so that
; jc doesn't restart straight away: it jumps to "showy" to display y first.
; The next sum (233 + 144) overflows too, and that jc restarts.
start:  ldi 1
        sta y           ; y = 1
        ldi 0           ; A = x = 0
loop:   out             ; show x
        add y
        jc showy        ; x + y overflowed: still show y, then restart
        sta z           ; z = x + y
showy:  lda y
        out             ; show y
        add z
        jc start        ; y + z overflowed: start over
        sta y           ; y = y + z
        lda z           ; A = z, the next x
        jmp loop
y:      db 0
z:      db 0
