// push constant 111
@111
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 333
@333
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 888
@888
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop static 8
@SP
AM=M-1
D=M
@StaticTest.8
M=D
// pop static 3
@SP
AM=M-1
D=M
@StaticTest.3
M=D
// pop static 1
@SP
AM=M-1
D=M
@StaticTest.1
M=D
// push static 3
@StaticTest.3
D=M
@SP
A=M
M=D
@SP
M=M+1
// push static 1
@StaticTest.1
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// push static 8
@StaticTest.8
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
