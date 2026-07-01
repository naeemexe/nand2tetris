// push constant 3030
@3030
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
// push constant 3040
@3040
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
// push constant 32
@32
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop this 2
@2
D=A
@THIS
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
// push constant 46
@46
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop that 6
@6
D=A
@THAT
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
// push pointer 0
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
// push pointer 1
@THAT
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
// push this 2
@2
D=A
@THIS
A=D+M
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
// push that 6
@6
D=A
@THAT
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
