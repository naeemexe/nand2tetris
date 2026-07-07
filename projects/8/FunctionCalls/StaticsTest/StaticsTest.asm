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
// function Class1.set 0
(Class1.set)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// pop static 0
@SP
AM=M-1
D=M
@Class1.0
M=D
// push argument 1
@1
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// pop static 1
@SP
AM=M-1
D=M
@Class1.1
M=D
// push constant 0
@SP
A=M
M=0
@SP
M=M+1
// return
@$$RETURN
0;JMP
// function Class1.get 0
(Class1.get)
// push static 0
@Class1.0
D=M
@SP
A=M
M=D
@SP
M=M+1
// push static 1
@Class1.1
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
// return
@$$RETURN
0;JMP
// function Class2.set 0
(Class2.set)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// pop static 0
@SP
AM=M-1
D=M
@Class2.0
M=D
// push argument 1
@1
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// pop static 1
@SP
AM=M-1
D=M
@Class2.1
M=D
// push constant 0
@SP
A=M
M=0
@SP
M=M+1
// return
@$$RETURN
0;JMP
// function Class2.get 0
(Class2.get)
// push static 0
@Class2.0
D=M
@SP
A=M
M=D
@SP
M=M+1
// push static 1
@Class2.1
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
// return
@$$RETURN
0;JMP
// function Sys.init 0
(Sys.init)
// push constant 6
@6
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 8
@8
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Class1.set 2
// call Class1.set 2
@2
D=A
@R13
M=D
@Class1.set
D=A
@R14
M=D
@Sys.init$ret.2
D=A
@$$CALL
0;JMP
(Sys.init$ret.2)
// pop temp 0
@SP
AM=M-1
D=M
@R5
M=D
// push constant 23
@23
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 15
@15
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Class2.set 2
// call Class2.set 2
@2
D=A
@R13
M=D
@Class2.set
D=A
@R14
M=D
@Sys.init$ret.3
D=A
@$$CALL
0;JMP
(Sys.init$ret.3)
// pop temp 0
@SP
AM=M-1
D=M
@R5
M=D
// call Class1.get 0
// call Class1.get 0
@0
D=A
@R13
M=D
@Class1.get
D=A
@R14
M=D
@Sys.init$ret.4
D=A
@$$CALL
0;JMP
(Sys.init$ret.4)
// call Class2.get 0
// call Class2.get 0
@0
D=A
@R13
M=D
@Class2.get
D=A
@R14
M=D
@Sys.init$ret.5
D=A
@$$CALL
0;JMP
(Sys.init$ret.5)
// label END
(Sys.init$END)
// goto END
@Sys.init$END
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
