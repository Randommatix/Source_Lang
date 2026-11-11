from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    line: int
    column: int


class LexerError(Exception):
    pass


class Lexer:
    KEYWORDS = {
        "return": "RETURN",
        "if": "IF",
        "elif": "ELIF",
        "true": "TRUE",
        "false": "FALSE"
    }

    TWO = {"==", "!=", "<=", ">=", "&&", "||"}
    SINGLE = set("{}(),.:+-*/%!=<>")

    def tokenize(self, source):
        result = []
        indents = []
        pending_indent = False
        brace_depth = 0
        lines = source.splitlines()

        for line_no, line in enumerate(lines, 1):
            stripped = line.lstrip(" ")

            if not stripped or stripped.startswith("//"):
                continue

            indent = len(line) - len(stripped)

            if "\t" in line[:indent]:
                raise LexerError(
                    f"No se permiten tabulaciones en línea {line_no}"
                )

            if pending_indent:
                if indents and indent <= indents[-1]:
                    raise LexerError(
                        f"Se esperaba un bloque indentado en línea {line_no}"
                    )

                indents.append(indent)
                result.append(Token("INDENT", indent, line_no, 1))
                pending_indent = False

            elif indents and indent < indents[-1]:
                while indents and indent < indents[-1]:
                    indents.pop()
                    result.append(
                        Token(
                            "DEDENT",
                            indents[-1] if indents else 0,
                            line_no,
                            1
                        )
                    )

                if indents and indent != indents[-1]:
                    raise LexerError(
                        f"Indentación inconsistente en línea {line_no}"
                    )

                if not indents and indent != 0 and brace_depth == 0:
                    raise LexerError(
                        f"Indentación inconsistente en línea {line_no}"
                    )

            elif not indents and indent > 0 and brace_depth == 0:
                raise LexerError(
                    f"Indentación inesperada en línea {line_no}"
                )

            i = indent
            line_has_colon = False

            while i < len(line):
                ch = line[i]

                if ch in " \r":
                    i += 1
                    continue

                if ch == "\t":
                    raise LexerError(
                        f"Tabulación inesperada en línea {line_no}"
                    )

                if line.startswith("//", i):
                    break

                if line.startswith("#!import", i):
                    end = i + 8

                    if end < len(line) and (
                        line[end].isalnum() or line[end] == "_"
                    ):
                        raise LexerError(
                            f"Directiva desconocida en línea {line_no}"
                        )

                    result.append(
                        Token("IMPORT", "#!import", line_no, i + 1)
                    )
                    i = end
                    continue

                if ch in "\"'":
                    quote = ch
                    start = i
                    i += 1
                    value = []

                    while i < len(line) and line[i] != quote:
                        if line[i] == "\\":
                            i += 1

                            if i >= len(line):
                                raise LexerError(
                                    f"Escape incompleto en línea {line_no}"
                                )

                            value.append({
                                "n": "\n",
                                "t": "\t",
                                "r": "\r"
                            }.get(line[i], line[i]))
                        else:
                            value.append(line[i])

                        i += 1

                    if i >= len(line):
                        raise LexerError(
                            f"Cadena sin cerrar en línea {line_no}"
                        )

                    i += 1
                    result.append(
                        Token("STRING", "".join(value), line_no, start + 1)
                    )
                    continue

                if ch.isdigit():
                    start = i

                    while i < len(line) and line[i].isdigit():
                        i += 1

                    if (
                        i + 1 < len(line)
                        and line[i] == "."
                        and line[i + 1].isdigit()
                    ):
                        i += 1

                        while i < len(line) and line[i].isdigit():
                            i += 1

                        value = float(line[start:i])
                    else:
                        value = int(line[start:i])

                    result.append(
                        Token("NUMBER", value, line_no, start + 1)
                    )
                    continue

                if ch.isalpha() or ch == "_":
                    start = i

                    while i < len(line) and (
                        line[i].isalnum() or line[i] == "_"
                    ):
                        i += 1

                    word = line[start:i]

                    result.append(
                        Token(
                            self.KEYWORDS.get(word, "IDENT"),
                            word,
                            line_no,
                            start + 1
                        )
                    )
                    continue

                pair = line[i:i + 2]

                if pair in self.TWO:
                    result.append(Token(pair, pair, line_no, i + 1))
                    i += 2
                    continue

                if ch in self.SINGLE:
                    result.append(
                        Token(ch, ch, line_no, i + 1)
                    )

                    if ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1

                        if brace_depth < 0:
                            raise LexerError(
                                f"Llave de cierre inesperada en línea {line_no}"
                            )
                    elif ch == ":":
                        line_has_colon = True

                    i += 1
                    continue

                raise LexerError(
                    f"Carácter inesperado {ch!r} "
                    f"en línea {line_no}, columna {i + 1}"
                )

            result.append(
                Token("NEWLINE", "\n", line_no, len(line) + 1)
            )

            if line_has_colon:
                pending_indent = True

        if pending_indent:
            raise LexerError("Se esperaba un bloque después de ':'")

        if brace_depth != 0:
            raise LexerError("Hay llaves sin cerrar")

        while indents:
            indents.pop()
            result.append(
                Token(
                    "DEDENT",
                    indents[-1] if indents else 0,
                    len(lines) + 1,
                    1
                )
            )

        result.append(
            Token("EOF", None, len(lines) + 1, 1)
        )

        return result


def tokenize(source):
    return Lexer().tokenize(source)