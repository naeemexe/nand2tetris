#!/usr/bin/env python3
"""
Jack syntax analyzer (Nand2Tetris project 10).

    python3 jack_analyzer.py Square/            ->  Square/output/*.xml
    python3 jack_analyzer.py Square/Main.jack   ->  Square/output/Main.xml

For every Xxx.jack writes two files into an output/ folder (so the course's
own Xxx.xml compare files are never overwritten):

    XxxT.xml  - the flat token stream          (checks the tokenizer)
    Xxx.xml   - the full parse tree            (checks the parser)

The parser is a hand-written RECURSIVE DESCENT parser: one method per rule
of the Jack grammar. Each method consumes exactly the tokens its rule
covers, calling the methods of the sub-rules it contains. The XML nesting
is a direct picture of that call stack.

Only one rule needs to look ahead more than one token: inside a term, an
identifier could be a plain variable, an array access 'a[...]', or a call
'f(...)' / 'X.f(...)'. Peeking at the token AFTER the identifier decides.
"""
import sys
from pathlib import Path

from jack_tokenizer import Token, tokenize, tokens_to_xml, xml_escape

OPS = set("+-*/&|<>=")
UNARY_OPS = set("-~")
KEYWORD_CONSTANTS = {"true", "false", "null", "this"}


class XmlParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.lines: list[str] = []
        self.depth = 0

    # ---- token helpers --------------------------------------------------
    @property
    def tok(self) -> Token:
        if self.pos >= len(self.tokens):
            raise SyntaxError("unexpected end of file")
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token | None:
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else None

    def at(self, *values) -> bool:
        return self.pos < len(self.tokens) and self.tok.value in values \
            and self.tok.type in ("keyword", "symbol")

    def eat(self, expected=None, type_=None) -> Token:
        """Consume the current token (checking it if asked) and emit it as XML."""
        t = self.tok
        if expected is not None and (t.value not in expected if isinstance(expected, (set, tuple)) else t.value != expected):
            raise SyntaxError(f"line {t.line}: expected {expected!r}, got {t.value!r}")
        if type_ is not None and t.type != type_:
            raise SyntaxError(f"line {t.line}: expected {type_}, got {t.type} {t.value!r}")
        self.leaf(t)
        self.pos += 1
        return t

    # ---- xml helpers ----------------------------------------------------
    def leaf(self, t: Token):
        self.lines.append("  " * self.depth + f"<{t.type}> {xml_escape(t.value)} </{t.type}>")

    def open(self, tag):
        self.lines.append("  " * self.depth + f"<{tag}>")
        self.depth += 1

    def close(self, tag):
        self.depth -= 1
        self.lines.append("  " * self.depth + f"</{tag}>")

    # ---- program structure ----------------------------------------------
    # class: 'class' className '{' classVarDec* subroutineDec* '}'
    def compile_class(self):
        self.open("class")
        self.eat("class")
        self.eat(type_="identifier")
        self.eat("{")
        while self.at("static", "field"):
            self.compile_class_var_dec()
        while self.at("constructor", "function", "method"):
            self.compile_subroutine()
        self.eat("}")
        self.close("class")

    def eat_type(self):
        if self.at("int", "char", "boolean"):
            self.eat()
        else:
            self.eat(type_="identifier")      # a class name

    # classVarDec: ('static'|'field') type varName (',' varName)* ';'
    def compile_class_var_dec(self):
        self.open("classVarDec")
        self.eat({"static", "field"})
        self.eat_type()
        self.eat(type_="identifier")
        while self.at(","):
            self.eat(",")
            self.eat(type_="identifier")
        self.eat(";")
        self.close("classVarDec")

    # subroutineDec: ('constructor'|'function'|'method') ('void'|type) name '(' parameterList ')' subroutineBody
    def compile_subroutine(self):
        self.open("subroutineDec")
        self.eat({"constructor", "function", "method"})
        if self.at("void"):
            self.eat("void")
        else:
            self.eat_type()
        self.eat(type_="identifier")
        self.eat("(")
        self.compile_parameter_list()
        self.eat(")")
        self.compile_subroutine_body()
        self.close("subroutineDec")

    # parameterList: ((type varName) (',' type varName)*)?
    def compile_parameter_list(self):
        self.open("parameterList")
        if not self.at(")"):
            self.eat_type()
            self.eat(type_="identifier")
            while self.at(","):
                self.eat(",")
                self.eat_type()
                self.eat(type_="identifier")
        self.close("parameterList")

    # subroutineBody: '{' varDec* statements '}'
    def compile_subroutine_body(self):
        self.open("subroutineBody")
        self.eat("{")
        while self.at("var"):
            self.compile_var_dec()
        self.compile_statements()
        self.eat("}")
        self.close("subroutineBody")

    # varDec: 'var' type varName (',' varName)* ';'
    def compile_var_dec(self):
        self.open("varDec")
        self.eat("var")
        self.eat_type()
        self.eat(type_="identifier")
        while self.at(","):
            self.eat(",")
            self.eat(type_="identifier")
        self.eat(";")
        self.close("varDec")

    # ---- statements -----------------------------------------------------
    def compile_statements(self):
        self.open("statements")
        while True:
            if self.at("let"):
                self.compile_let()
            elif self.at("if"):
                self.compile_if()
            elif self.at("while"):
                self.compile_while()
            elif self.at("do"):
                self.compile_do()
            elif self.at("return"):
                self.compile_return()
            else:
                break
        self.close("statements")

    # let varName ('[' expression ']')? '=' expression ';'
    def compile_let(self):
        self.open("letStatement")
        self.eat("let")
        self.eat(type_="identifier")
        if self.at("["):
            self.eat("[")
            self.compile_expression()
            self.eat("]")
        self.eat("=")
        self.compile_expression()
        self.eat(";")
        self.close("letStatement")

    # if '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
    def compile_if(self):
        self.open("ifStatement")
        self.eat("if")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        if self.at("else"):
            self.eat("else")
            self.eat("{")
            self.compile_statements()
            self.eat("}")
        self.close("ifStatement")

    # while '(' expression ')' '{' statements '}'
    def compile_while(self):
        self.open("whileStatement")
        self.eat("while")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        self.close("whileStatement")

    # do subroutineCall ';'
    def compile_do(self):
        self.open("doStatement")
        self.eat("do")
        self.compile_subroutine_call()
        self.eat(";")
        self.close("doStatement")

    # return expression? ';'
    def compile_return(self):
        self.open("returnStatement")
        self.eat("return")
        if not self.at(";"):
            self.compile_expression()
        self.eat(";")
        self.close("returnStatement")

    # ---- expressions ----------------------------------------------------
    # expression: term (op term)*
    def compile_expression(self):
        self.open("expression")
        self.compile_term()
        while self.tok.type == "symbol" and self.tok.value in OPS:
            self.eat()
            self.compile_term()
        self.close("expression")

    # term: integerConstant | stringConstant | keywordConstant | varName |
    #       varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    def compile_term(self):
        self.open("term")
        t = self.tok
        if t.type in ("integerConstant", "stringConstant"):
            self.eat()
        elif t.type == "keyword" and t.value in KEYWORD_CONSTANTS:
            self.eat()
        elif self.at("("):
            self.eat("(")
            self.compile_expression()
            self.eat(")")
        elif t.type == "symbol" and t.value in UNARY_OPS:
            self.eat()
            self.compile_term()
        elif t.type == "identifier":
            nxt = self.peek()                         # the one-token lookahead
            if nxt and nxt.value == "[":
                self.eat()
                self.eat("[")
                self.compile_expression()
                self.eat("]")
            elif nxt and nxt.value in ("(", "."):
                self.compile_subroutine_call()
            else:
                self.eat()
        else:
            raise SyntaxError(f"line {t.line}: unexpected {t.value!r} in expression")
        self.close("term")

    # subroutineCall: name '(' expressionList ')' | (className|varName) '.' name '(' expressionList ')'
    # (no XML tag of its own - the spec says so)
    def compile_subroutine_call(self):
        self.eat(type_="identifier")
        if self.at("."):
            self.eat(".")
            self.eat(type_="identifier")
        self.eat("(")
        self.compile_expression_list()
        self.eat(")")

    # expressionList: (expression (',' expression)*)?
    def compile_expression_list(self):
        self.open("expressionList")
        if not self.at(")"):
            self.compile_expression()
            while self.at(","):
                self.eat(",")
                self.compile_expression()
        self.close("expressionList")


def analyze_file(path: Path, outdir: Path):
    tokens = tokenize(path.read_text())
    (outdir / f"{path.stem}T.xml").write_text(tokens_to_xml(tokens))
    parser = XmlParser(tokens)
    parser.compile_class()
    if parser.pos != len(tokens):
        raise SyntaxError(f"{path}: junk after the end of the class")
    (outdir / f"{path.stem}.xml").write_text("\n".join(parser.lines) + "\n")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: jack_analyzer.py (File.jack | Directory)")
    target = Path(sys.argv[1])
    files = sorted(target.glob("*.jack")) if target.is_dir() else [target]
    outdir = (target if target.is_dir() else target.parent) / "output"
    outdir.mkdir(exist_ok=True)
    for f in files:
        analyze_file(f, outdir)
        print(f"{f} -> {outdir}/{f.stem}.xml, {f.stem}T.xml")


if __name__ == "__main__":
    main()
