from dataclasses import dataclass, field
from typing import Any
from lexer import Lexer

class ParserError(Exception):
    pass

@dataclass
class Program:
    imports: list[str] = field(default_factory=list)
    declarations: list[Any] = field(default_factory=list)

@dataclass
class SourceDecl:
    name: str
    body: list[Any]

@dataclass
class FunctionDecl:
    name: str
    sources: list[str]
    parameters: list[str]
    body: list[Any]

@dataclass
class ElifBranch:
    condition: Any
    body: list[Any]

@dataclass
class IfStmt:
    condition: Any
    body: list[Any]
    elif_branches: list[Any] = field(default_factory=list)

@dataclass
class ReturnStmt:
    value: Any = None

@dataclass
class ExprStmt:
    expression: Any

@dataclass
class Name:
    value: str

@dataclass
class Variable:
    name: str
    scope: str

@dataclass
class Assign:
    target: Any
    value: Any

@dataclass
class Literal:
    value: Any

@dataclass
class Member:
    object: Any
    name: str

@dataclass
class CallExpr:
    callee: Any
    arguments: list[Any]

@dataclass
class Unary:
    operator: str
    operand: Any

@dataclass
class Binary:
    left: Any
    operator: str
    right: Any

class Parser:
    PRECEDENCE = {"||":1, "&&":2, "==":3, "!=":3, "<":3, ">":3, "<=":3, ">=":3,
                  "+":4, "-":4, "*":5, "/":5, "%":5}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def cur(self):
        return self.tokens[self.pos]

    def check(self, *kinds):
        return self.cur().kind in kinds

    def take(self):
        token = self.cur()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def expect(self, kind):
        if not self.check(kind):
            t = self.cur()
            raise ParserError(f"Se esperaba {kind}, se encontró {t.kind} en línea {t.line}, columna {t.column}")
        return self.take()

    def newlines(self):
        while self.check("NEWLINE"):
            self.take()

    def parse(self):
        program = Program()
        self.newlines()
        while not self.check("EOF"):
            if self.check("IMPORT"):
                self.take()
                if self.check("STRING"):
                    program.imports.append(self.take().value)
                else:
                    program.imports.append(self.expect("IDENT").value)
            else:
                program.declarations.append(self.declaration())
            self.newlines()
        return program

    def declaration(self):
        if self.check("*"):
            self.take()
            name = self.expect("IDENT").value
            if self.check("{"):
                return self.source(name)
            return self.function(name, [])

        sources = []
        if self.check("("):
            self.take()
            sources.append(self.expect("IDENT").value)
            while self.check(","):
                self.take()
                sources.append(self.expect("IDENT").value)
            self.expect(")")
        elif self.check("IDENT"):
            sources.append(self.take().value)
        else:
            t = self.cur()
            raise ParserError(f"Declaración inesperada en línea {t.line}")

        name = self.expect("IDENT").value
        return self.function(name, sources)

    def is_declaration(self):
        if self.check("*"):
            return True

        if self.check("IDENT"):
            return (
                self.pos + 2 < len(self.tokens)
                and self.tokens[self.pos + 1].kind == "IDENT"
                and self.tokens[self.pos + 2].kind == "("
            )

        if self.check("("):
            pos = self.pos + 1
            depth = 1

            while pos < len(self.tokens) and depth:
                kind = self.tokens[pos].kind

                if kind == "(":
                    depth += 1
                elif kind == ")":
                    depth -= 1

                pos += 1

            return (
                depth == 0
                and pos + 1 < len(self.tokens)
                and self.tokens[pos].kind == "IDENT"
                and self.tokens[pos + 1].kind == "("
            )

        return False

    def source(self, name):
        self.expect("{")
        self.newlines()
        body = []

        while not self.check("}", "EOF"):
            if self.check("IF"):
                body.append(self.if_statement())
            elif self.is_declaration():
                body.append(self.declaration())
            elif self.check("IDENT"):
                body.append(self.statement())
            else:
                t = self.cur()
                raise ParserError(
                    f"Elemento no permitido en fuente, línea {t.line}"
                )

            self.newlines()

        self.expect("}")
        return SourceDecl(name, body)

    def function(self, name, sources):
        self.expect("(")
        params = []
        if not self.check(")"):
            params.append(self.expect("IDENT").value)
            while self.check(","):
                self.take()
                params.append(self.expect("IDENT").value)
        self.expect(")")
        self.expect("{")
        self.newlines()
        body = []
        while not self.check("}", "EOF"):
            body.append(self.statement())
            self.newlines()
        self.expect("}")
        return FunctionDecl(name, sources, params, body)

    def if_statement(self):
        self.expect("IF")
        original_condition = self.expression()
        self.expect(":")
        self.newlines()
        self.expect("INDENT")
        self.newlines()

        body = []

        while not self.check("DEDENT", "EOF"):
            body.append(self.statement())
            self.newlines()

        self.expect("DEDENT")

        branches = []

        while self.check("ELIF"):
            self.take()
            condition = self.expression()
            self.expect(":")
            self.newlines()
            self.expect("INDENT")
            self.newlines()

            branch_body = []

            while not self.check("DEDENT", "EOF"):
                branch_body.append(self.statement())
                self.newlines()

            self.expect("DEDENT")
            branches.append(ElifBranch(condition, branch_body))

        return IfStmt(original_condition, body, branches)

    def statement(self):
        if self.check("RETURN"):
            self.take()
            if self.check("NEWLINE", "}", "DEDENT", "EOF"):
                return ReturnStmt()
            return ReturnStmt(self.expression())
        if self.check("IF"):
            return self.if_statement()
        if self.check("*"):
            return self.declaration()

        expression = self.expression()

        if self.check("="):
            self.take()
            if not isinstance(expression, (Name, Variable)):
                t = self.cur()
                raise ParserError(
                    f"El destino de asignación debe ser una variable, "
                    f"línea {t.line}, columna {t.column}"
                )
            return Assign(expression, self.expression())

        return ExprStmt(expression)

    def expression(self, minimum=1):
        left = self.unary()
        while self.cur().kind in self.PRECEDENCE and self.PRECEDENCE[self.cur().kind] >= minimum:
            op = self.take().kind
            right = self.expression(self.PRECEDENCE[op] + 1)
            left = Binary(left, op, right)
        return left

    def unary(self):
        if self.check("!", "-", "+"):
            op = self.take().kind
            return Unary(op, self.unary())
        return self.postfix()

    def postfix(self):
        value = self.primary()
        while True:
            if self.check("."):
                self.take()
                value = Member(value, self.expect("IDENT").value)
            elif self.check("("):
                self.take()
                args = []
                if not self.check(")"):
                    args.append(self.expression())
                    while self.check(","):
                        self.take()
                        args.append(self.expression())
                self.expect(")")
                value = CallExpr(value, args)
            else:
                return value

    def primary(self):
        t = self.cur()
        if self.check("NUMBER", "STRING"):
            self.take()
            return Literal(t.value)
        if self.check("TRUE", "FALSE"):
            self.take()
            return Literal(t.kind == "TRUE")
        if self.check("IDENT") and t.value in ("l", "o"):
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].kind == "!":
                scope = "local" if t.value == "l" else "program"
                self.take()
                self.take()
                name = self.expect("IDENT").value
                return Variable(name, scope)
        if self.check("IDENT"):
            self.take()
            return Name(t.value)
        if self.check("("):
            self.take()
            value = self.expression()
            self.expect(")")
            return value
        raise ParserError(f"Expresión inesperada {t.kind} en línea {t.line}, columna {t.column}")

def parse(source: str) -> Program:
    return Parser(Lexer().tokenize(source)).parse()