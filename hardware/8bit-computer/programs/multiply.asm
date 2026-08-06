; product = x * y by repeated addition (there is no multiply instruction).
; The trick for the loop test: SUB sets the carry flag when there was NO
; borrow, i.e. when y >= 1 before subtracting. So "jc" means "keep going".
loop:     lda y
          sub one         ; A = y - 1
          jc again        ; y was >= 1 -> one more addition
          lda product     ; y was 0 -> done
          out
          hlt
again:    sta y           ; y = y - 1
          lda product
          add x
          sta product     ; product = product + x
          jmp loop
one:      db 1
product:  db 0
x:        db 7
y:        db 8
