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
// function Main.fibonacci 0
(Main.fibonacci)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 2
@2
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@$cmp.ret.2
D=A
@$$LT
0;JMP
($cmp.ret.2)
// if-goto N_LT_2
@SP
AM=M-1
D=M
@Main.fibonacci$N_LT_2
D;JNE
// goto N_GE_2
@Main.fibonacci$N_GE_2
0;JMP
// label N_LT_2
(Main.fibonacci$N_LT_2)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// return
@$$RETURN
0;JMP
// label N_GE_2
(Main.fibonacci$N_GE_2)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 2
@2
D=A
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
// call Main.fibonacci 1
// call Main.fibonacci 1
@1
D=A
@R13
M=D
@Main.fibonacci
D=A
@R14
M=D
@Main.fibonacci$ret.3
D=A
@$$CALL
0;JMP
(Main.fibonacci$ret.3)
// push argument 0
@ARG
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 1
@SP
A=M
M=1
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// call Main.fibonacci 1
// call Main.fibonacci 1
@1
D=A
@R13
M=D
@Main.fibonacci
D=A
@R14
M=D
@Main.fibonacci$ret.4
D=A
@$$CALL
0;JMP
(Main.fibonacci$ret.4)
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// return
@$$RETURN
0;JMP
// function Sys.init 0
(Sys.init)
// push constant 4
@4
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Main.fibonacci 1
// call Main.fibonacci 1
@1
D=A
@R13
M=D
@Main.fibonacci
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
