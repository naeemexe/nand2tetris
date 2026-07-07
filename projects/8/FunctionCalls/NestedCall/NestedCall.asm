// bootstrap: SP = 256; call Sys.init
@256
D=A
@SP
M=D
// call Sys.init 0
@0
D=A
@R13
M=D
@Sys.init
D=A
@R14
M=D
@boot$ret.1
D=A
@$$CALL
0;JMP
(boot$ret.1)
// function Sys.init 0
(Sys.init)
// push constant 4000
@4000
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 0
@SP
AM=M-1
D=M
@THIS
M=D
// push constant 5000
@5000
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 1
@SP
AM=M-1
D=M
@THAT
M=D
// call Sys.main 0
// call Sys.main 0
@0
D=A
@R13
M=D
@Sys.main
D=A
@R14
M=D
@Sys.init$ret.2
D=A
@$$CALL
0;JMP
(Sys.init$ret.2)
// pop temp 1
@SP
AM=M-1
D=M
@R6
M=D
// label LOOP
(Sys.init$LOOP)
// goto LOOP
@Sys.init$LOOP
0;JMP
// function Sys.main 5
(Sys.main)
@SP
A=M
M=0
A=A+1
M=0
A=A+1
M=0
A=A+1
M=0
A=A+1
M=0
A=A+1
D=A
@SP
M=D
// push constant 4001
@4001
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 0
@SP
AM=M-1
D=M
@THIS
M=D
// push constant 5001
@5001
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 1
@SP
AM=M-1
D=M
@THAT
M=D
// push constant 200
@200
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop local 1
@1
D=A
@LCL
A=D+M
D=A
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// push constant 40
@40
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop local 2
@2
D=A
@LCL
A=D+M
D=A
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// push constant 6
@6
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop local 3
@3
D=A
@LCL
A=D+M
D=A
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// push constant 123
@123
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Sys.add12 1
// call Sys.add12 1
@1
D=A
@R13
M=D
@Sys.add12
D=A
@R14
M=D
@Sys.main$ret.3
D=A
@$$CALL
0;JMP
(Sys.main$ret.3)
// pop temp 0
@SP
AM=M-1
D=M
@R5
M=D
// push local 0
@LCL
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push local 1
@1
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push local 2
@2
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push local 3
@3
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push local 4
@4
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// return
@$$RETURN
0;JMP
// function Sys.add12 0
(Sys.add12)
// push constant 4002
@4002
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 0
@SP
AM=M-1
D=M
@THIS
M=D
// push constant 5002
@5002
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop pointer 1
@SP
AM=M-1
D=M
@THAT
M=D
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 12
@12
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// return
@$$RETURN
0;JMP
// ---- end of program: park here so we never fall into the runtime
($$END)
@$$END
0;JMP
// $$EQ: x = (x eq y) ? -1 : 0
($$EQ)
@R15
M=D
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@$$EQ.TRUE
D;JEQ
@R15
A=M
0;JMP
($$EQ.TRUE)
@SP
A=M-1
M=-1
@R15
A=M
0;JMP
// $$GT: x = (x gt y) ? -1 : 0
($$GT)
@R15
M=D
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@$$GT.TRUE
D;JGT
@R15
A=M
0;JMP
($$GT.TRUE)
@SP
A=M-1
M=-1
@R15
A=M
0;JMP
// $$LT: x = (x lt y) ? -1 : 0
($$LT)
@R15
M=D
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@$$LT.TRUE
D;JLT
@R15
A=M
0;JMP
($$LT.TRUE)
@SP
A=M-1
M=-1
@R15
A=M
0;JMP
// $$CALL: push frame, reposition ARG and LCL, jump
($$CALL)
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@SP
D=M
@R13
D=D-M
@5
D=D-A
@ARG
M=D
@SP
D=M
@LCL
M=D
@R14
A=M
0;JMP
// $$RETURN: restore caller's frame
($$RETURN)
@LCL
D=M
@R13
M=D
@5
A=D-A
D=M
@R14
M=D
@SP
AM=M-1
D=M
@ARG
A=M
M=D
@ARG
D=M+1
@SP
M=D
@R13
AM=M-1
D=M
@THAT
M=D
@R13
AM=M-1
D=M
@THIS
M=D
@R13
AM=M-1
D=M
@ARG
M=D
@R13
AM=M-1
D=M
@LCL
M=D
@R14
A=M
0;JMP
