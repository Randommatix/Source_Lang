import sys
from pathlib import Path

from interpreter import Interpreter, RuntimeErrorLang
from parser import ParserError
from lexer import LexerError


def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <archivo>")
        return 1

    filename = Path(sys.argv[1])

    if not filename.is_file():
        print(f"Error: no existe el archivo '{filename}'")
        return 1

    try:
        interpreter = Interpreter()
        result = interpreter.execute_file(filename)

        if result is not None:
            print(result)

        return 0

    except (LexerError, ParserError, RuntimeErrorLang) as error:
        print(f"Error: {error}")
        return 1

    except Exception as error:
        print(f"Error interno: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())