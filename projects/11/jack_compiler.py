#!/usr/bin/env python3
"""
Jack compiler (Nand2Tetris project 11).

    python3 jack_compiler.py Pong/            ->  Pong/*.vm  (one per .jack)
    python3 jack_compiler.py Pong/Main.jack   ->  Pong/Main.vm

Same recursive-descent shape as the project 10 analyzer, but instead of
printing XML each rule emits VM code. Two new pieces make that possible:

  SymbolTable  - every variable name maps to (type, kind, index).
                 kind -> VM segment:  static->static  field->this
                                      arg->argument   var->local
                 So 'x' in the source becomes e.g. 'push local 2'.

  VMWriter     - tiny helper that formats VM commands.

How each construct is lowered (the core of the compiler):

  let x = e;          e ; pop x
  let a[i] = e;       push a ; i ; add ; e ; pop temp 0 ; pop pointer 1 ;
                      push temp 0 ; pop that 0
                      (e is computed BEFORE 'that' is set, because e itself
                       might use 'that' for another array access)
  if (c) {S1} else {S2}
                      c ; not ; if-goto ELSE ; S1 ; goto END ;
                      label ELSE ; S2 ; label END
  while (c) {S}       label TOP ; c ; not ; if-goto END ; S ; goto TOP ; label END
  do f(...);          f(...) ; pop temp 0          (throw the return value away)
  return;             push constant 0 ; return     (void still returns *something*)

  obj.m(a, b)         push obj ; a ; b ; call Class.m 3   (object is hidden arg 0)
  m(a, b)             push pointer 0 ; a ; b ; call ThisClass.m 3
  Class.f(a, b)       a ; b ; call Class.f 2

  constructor         push constant nFields ; call Memory.alloc 1 ; pop pointer 0
  method              push argument 0 ; pop pointer 0     (anchor 'this')
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "10"))
from jack_tokenizer import Token, tokenize  # noqa: E402

KIND_SEGMENT = {"static": "static", "field": "this", "arg": "argument", "var": "local"}
BINARY_OPS = {
    "+": "add", "-": "sub", "&": "and", "|": "or",
    "<": "lt", ">": "gt", "=": "eq",
    "*": "call Math.multiply 2", "/": "call Math.divide 2",
}
UNARY_OPS = {"-": "neg", "~": "not"}


class SymbolTable:
    """Two scopes: class (static/field) lives for the whole class,
    subroutine (arg/var) is reset at the start of every subroutine."""

    def __init__(self):
        self.class_scope: dict[str, tuple[str, str, int]] = {}
        self.sub_scope: dict[str, tuple[str, str, int]] = {}

    def start_subroutine(self):
        self.sub_scope = {}

    def define(self, name, type_, kind):
        scope = self.class_scope if kind in ("static", "field") else self.sub_scope
        if name in scope:
            raise SyntaxError(f"'{name}' is declared twice")
        scope[name] = (type_, kind, self.count(kind))

    def count(self, kind):
        scope = self.class_scope if kind in ("static", "field") else self.sub_scope
        return sum(1 for (_, k, _) in scope.values() if k == kind)

    def lookup(self, name):
        """(type, kind, index) or None. Subroutine scope shadows class scope."""
        return self.sub_scope.get(name) or self.class_scope.get(name)


class Compiler:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.vm: list[str] = []
        self.symbols = SymbolTable()
        self.class_name = ""
        self.label_count = 0

    # ---- token helpers (same as the analyzer) ---------------------------
    @property
    def tok(self) -> Token:
        if self.pos >= len(self.tokens):
            raise SyntaxError("unexpected end of file")
        return self.tokens[self.pos]

    def peek(self, offset=1):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else None

    def at(self, *values):
        return self.pos < len(self.tokens) and self.tok.type in ("keyword", "symbol") \
            and self.tok.value in values

    def eat(self, expected=None, type_=None) -> str:
        t = self.tok
        if expected is not None and t.value != expected:
            raise SyntaxError(f"line {t.line}: expected {expected!r}, got {t.value!r}")
        if type_ is not None and t.type != type_:
            raise SyntaxError(f"line {t.line}: expected {type_}, got {t.value!r}")
        self.pos += 1
        return t.value

    def eat_type(self) -> str:
        if self.at("int", "char", "boolean"):
            return self.eat()
        return self.eat(type_="identifier")

    # ---- VM writer -------------------------------------------------------
    def emit(self, line):
        self.vm.append(line)

    def new_label(self, kind):
        self.label_count += 1
        return f"{kind}{self.label_count}"

    def push_var(self, name):
        _, kind, index = self.resolve(name)
        self.emit(f"push {KIND_SEGMENT[kind]} {index}")

    def pop_var(self, name):
        _, kind, index = self.resolve(name)
        self.emit(f"pop {KIND_SEGMENT[kind]} {index}")

    def resolve(self, name):
        entry = self.symbols.lookup(name)
        if entry is None:
            raise SyntaxError(f"line {self.tokens[self.pos - 1].line}: undeclared variable '{name}'")
        return entry

    # ---- program structure -----------------------------------------------
    def compile_class(self):
        self.eat("class")
        self.class_name = self.eat(type_="identifier")
        self.eat("{")
        while self.at("static", "field"):
            self.compile_class_var_dec()
        while self.at("constructor", "function", "method"):
            self.compile_subroutine()
        self.eat("}")

    def compile_class_var_dec(self):
        kind = self.eat()
        type_ = self.eat_type()
        self.symbols.define(self.eat(type_="identifier"), type_, kind)
        while self.at(","):
            self.eat(",")
            self.symbols.define(self.eat(type_="identifier"), type_, kind)
        self.eat(";")

    def compile_subroutine(self):
        kind = self.eat()                        # constructor | function | method
        self.symbols.start_subroutine()
        self.label_count = 0
        if self.at("void"):
            self.eat()
        else:
            self.eat_type()
        name = self.eat(type_="identifier")
        if kind == "method":
            # 'this' is secretly argument 0 - define it first so real args start at 1
            self.symbols.define("this", self.class_name, "arg")

        self.eat("(")
        self.compile_parameter_list()
        self.eat(")")

        self.eat("{")
        while self.at("var"):
            self.compile_var_dec()
        # Only now do we know how many locals there are.
        self.emit(f"function {self.class_name}.{name} {self.symbols.count('var')}")
        if kind == "constructor":
            self.emit(f"push constant {self.symbols.count('field')}")
            self.emit("call Memory.alloc 1")
            self.emit("pop pointer 0")
        elif kind == "method":
            self.emit("push argument 0")
            self.emit("pop pointer 0")
        self.compile_statements()
        self.eat("}")

    def compile_parameter_list(self):
        if self.at(")"):
            return
        while True:
            type_ = self.eat_type()
            self.symbols.define(self.eat(type_="identifier"), type_, "arg")
            if not self.at(","):
                break
            self.eat(",")

    def compile_var_dec(self):
        self.eat("var")
        type_ = self.eat_type()
        self.symbols.define(self.eat(type_="identifier"), type_, "var")
        while self.at(","):
            self.eat(",")
            self.symbols.define(self.eat(type_="identifier"), type_, "var")
        self.eat(";")

    # ---- statements ------------------------------------------------------
    def compile_statements(self):
        handlers = {"let": self.compile_let, "if": self.compile_if,
                    "while": self.compile_while, "do": self.compile_do,
                    "return": self.compile_return}
        while self.tok.value in handlers and self.tok.type == "keyword":
            handlers[self.tok.value]()

    def compile_let(self):
        self.eat("let")
        name = self.eat(type_="identifier")
        if self.at("["):
            self.push_var(name)                  # base address
            self.eat("[")
            self.compile_expression()            # index
            self.eat("]")
            self.emit("add")                     # target address sits on the stack
            self.eat("=")
            self.compile_expression()            # value
            self.emit("pop temp 0")
            self.emit("pop pointer 1")           # THAT = target address
            self.emit("push temp 0")
            self.emit("pop that 0")
        else:
            self.eat("=")
            self.compile_expression()
            self.pop_var(name)
        self.eat(";")

    def compile_if(self):
        else_label, end_label = self.new_label("IF_ELSE"), self.new_label("IF_END")
        self.eat("if")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.emit("not")
        self.emit(f"if-goto {else_label}")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        if self.at("else"):
            self.emit(f"goto {end_label}")
            self.emit(f"label {else_label}")
            self.eat("else")
            self.eat("{")
            self.compile_statements()
            self.eat("}")
            self.emit(f"label {end_label}")
        else:
            self.emit(f"label {else_label}")     # no else: just fall out

    def compile_while(self):
        top, end = self.new_label("WHILE_TOP"), self.new_label("WHILE_END")
        self.emit(f"label {top}")
        self.eat("while")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.emit("not")
        self.emit(f"if-goto {end}")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        self.emit(f"goto {top}")
        self.emit(f"label {end}")

    def compile_do(self):
        self.eat("do")
        self.compile_subroutine_call()
        self.emit("pop temp 0")
        self.eat(";")

    def compile_return(self):
        self.eat("return")
        if self.at(";"):
            self.emit("push constant 0")
        else:
            self.compile_expression()
        self.emit("return")
        self.eat(";")

    # ---- expressions -----------------------------------------------------
    def compile_expression(self):
        # Jack has no operator precedence: strictly left to right.
        self.compile_term()
        while self.tok.type == "symbol" and self.tok.value in BINARY_OPS:
            op = self.eat()
            self.compile_term()
            self.emit(BINARY_OPS[op])

    def compile_term(self):
        t = self.tok
        if t.type == "integerConstant":
            self.emit(f"push constant {self.eat()}")
        elif t.type == "stringConstant":
            text = self.eat()
            self.emit(f"push constant {len(text)}")
            self.emit("call String.new 1")
            for ch in text:
                self.emit(f"push constant {ord(ch)}")
                self.emit("call String.appendChar 2")   # returns the string, so it chains
        elif t.type == "keyword":
            word = self.eat()
            if word == "true":
                self.emit("push constant 0")
                self.emit("not")                         # true is -1 = all ones
            elif word in ("false", "null"):
                self.emit("push constant 0")
            elif word == "this":
                self.emit("push pointer 0")
            else:
                raise SyntaxError(f"line {t.line}: '{word}' can't be used in an expression")
        elif self.at("("):
            self.eat("(")
            self.compile_expression()
            self.eat(")")
        elif t.type == "symbol" and t.value in UNARY_OPS:
            op = self.eat()
            self.compile_term()
            self.emit(UNARY_OPS[op])
        elif t.type == "identifier":
            nxt = self.peek()
            if nxt and nxt.value == "[":                 # array read: *(a + i)
                name = self.eat()
                self.push_var(name)
                self.eat("[")
                self.compile_expression()
                self.eat("]")
                self.emit("add")
                self.emit("pop pointer 1")
                self.emit("push that 0")
            elif nxt and nxt.value in ("(", "."):
                self.compile_subroutine_call()
            else:
                self.push_var(self.eat())
        else:
            raise SyntaxError(f"line {t.line}: unexpected {t.value!r} in expression")

    def compile_subroutine_call(self):
        first = self.eat(type_="identifier")
        n_args = 0
        if self.at("."):
            self.eat(".")
            method = self.eat(type_="identifier")
            entry = self.symbols.lookup(first)
            if entry:                                    # var.method(): push the object
                type_, kind, index = entry
                self.emit(f"push {KIND_SEGMENT[kind]} {index}")
                target = f"{type_}.{method}"
                n_args = 1
            else:                                        # Class.function()
                target = f"{first}.{method}"
        else:                                            # method(): call on 'this'
            self.emit("push pointer 0")
            target = f"{self.class_name}.{first}"
            n_args = 1
        self.eat("(")
        n_args += self.compile_expression_list()
        self.eat(")")
        self.emit(f"call {target} {n_args}")

    def compile_expression_list(self) -> int:
        if self.at(")"):
            return 0
        self.compile_expression()
        count = 1
        while self.at(","):
            self.eat(",")
            self.compile_expression()
            count += 1
        return count


def compile_file(path: Path) -> Path:
    tokens = tokenize(path.read_text())
    c = Compiler(tokens)
    try:
        c.compile_class()
        if c.pos != len(tokens):
            raise SyntaxError("junk after the end of the class")
    except SyntaxError as err:
        raise SystemExit(f"{path}: {err}")
    out = path.with_suffix(".vm")
    out.write_text("\n".join(c.vm) + "\n")
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: jack_compiler.py (File.jack | Directory)")
    target = Path(sys.argv[1])
    files = sorted(target.glob("*.jack")) if target.is_dir() else [target]
    for f in files:
        print(f"{f} -> {compile_file(f)}")


if __name__ == "__main__":
    main()
