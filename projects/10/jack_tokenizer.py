"""
Jack tokenizer (Nand2Tetris project 10, part 1).

Turns Jack source text into a flat list of Token(type, value). Five token
types, exactly as the language spec defines them:

    keyword          class constructor function method field static var
                     int char boolean void true false null this let do
                     if else while return
    symbol           { } ( ) [ ] . , ; + - * / & | < > = ~
    integerConstant  0 .. 32767
    stringConstant   "anything but a quote or newline"
    identifier       letters, digits, _ ; not starting with a digit

The whole thing is one regular expression with a named group per token
kind. re.finditer walks the source left to right and at each position
takes the first alternative that matches - comments and whitespace are
alternatives too, they're just thrown away.
"""
import re
from dataclasses import dataclass

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static", "var",
    "int", "char", "boolean", "void", "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
}
SYMBOLS = "{}()[].,;+-*/&|<>=~"

TOKEN_RE = re.compile(r"""
      (?P<comment>     //[^\n]*  |  /\*.*?\*/ )         # both comment styles (/** too)
    | (?P<space>       \s+ )
    | (?P<integer>     \d+ )
    | (?P<string>      "[^"\n]*" )
    | (?P<word>        [A-Za-z_][A-Za-z0-9_]* )         # keyword or identifier
    | (?P<symbol>      [{}()\[\].,;+\-*/&|<>=~] )
    | (?P<error>       . )                              # anything else is a mistake
""", re.VERBOSE | re.DOTALL)


@dataclass
class Token:
    type: str       # 'keyword' | 'symbol' | 'integerConstant' | 'stringConstant' | 'identifier'
    value: str
    line: int

    def __repr__(self):
        return f"{self.type}:{self.value}@{self.line}"


def tokenize(source: str) -> list[Token]:
    tokens = []
    line = 1
    for m in TOKEN_RE.finditer(source):
        kind, text = m.lastgroup, m.group()
        if kind == "integer":
            if int(text) > 32767:
                raise SyntaxError(f"line {line}: integer {text} is out of range")
            tokens.append(Token("integerConstant", text, line))
        elif kind == "string":
            tokens.append(Token("stringConstant", text[1:-1], line))
        elif kind == "word":
            tokens.append(Token("keyword" if text in KEYWORDS else "identifier", text, line))
        elif kind == "symbol":
            tokens.append(Token("symbol", text, line))
        elif kind == "error":
            raise SyntaxError(f"line {line}: unexpected character {text!r}")
        line += text.count("\n")
    return tokens


def xml_escape(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def tokens_to_xml(tokens: list[Token]) -> str:
    """The flat <tokens> listing used to check the tokenizer on its own (XxxT.xml)."""
    body = "".join(f"<{t.type}> {xml_escape(t.value)} </{t.type}>\n" for t in tokens)
    return f"<tokens>\n{body}</tokens>\n"
