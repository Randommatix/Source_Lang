from pathlib import Path

from parser import (
    parse,
    Program,
    SourceDecl,
    FunctionDecl,
    IfStmt,
    ElifBranch,
    ReturnStmt,
    ExprStmt,
    Name,
    Variable,
    Assign,
    Literal,
    Member,
    CallExpr,
    Unary,
    Binary
)


class RuntimeErrorLang(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value=None):
        self.value = value


class Environment:
    def __init__(self, parent=None, kind="normal"):
        self.parent = parent
        self.kind = kind
        self.values = {}
        self.local_values = {}
        self.functions = {}
        self.prefunctions = {}

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]

        if self.parent:
            return self.parent.get(name)

        raise RuntimeErrorLang(f"Variable desconocida: {name}")

    def get_local(self, name):
        if name not in self.local_values:
            raise RuntimeErrorLang(f"Variable local desconocida: {name}")
        return self.local_values[name]

    def assign_source(self, name, value):
        current = self

        while current is not None:
            if name in current.values:
                current.values[name] = value
                return

            current = current.parent

        current = self
        source_env = None

        while current is not None:
            if current.kind == "source":
                source_env = current
                break
            current = current.parent

        if source_env is not None:
            source_env.define(name, value)
        else:
            self.define(name, value)

    def define_function(self, name, function):
        self.functions[name] = function

    def get_function(self, name):
        if name in self.functions:
            return self.functions[name]

        if self.parent:
            return self.parent.get_function(name)

        return None


class SourceRuntime:
    def __init__(self, declaration, env):
        self.declaration = declaration
        self.env = env
        self.functions = {}
        self.exposed = set()
        self.exposed_variables = set()


class FunctionRuntime:
    def __init__(self, declaration, closure=None):
        self.declaration = declaration
        self.closure = closure


class SourceFunction:
    def __init__(self, runtime, name):
        self.runtime = runtime
        self.name = name


class Interpreter:
    def __init__(self):
        self.sources = {}
        self.global_env = Environment()
        self.program_env = Environment(kind="program")
        self.source_instances = {}
        self.loaded_files = set()
        self.loading_files = set()

    def reset_execution(self):
        self.program_env = Environment(kind="program")
        self.source_instances = {}

    def register_program(self, program):
        for declaration in program.declarations:
            if isinstance(declaration, SourceDecl):
                self.sources[declaration.name] = declaration

            elif isinstance(declaration, FunctionDecl):
                self.global_env.define_function(
                    declaration.name,
                    FunctionRuntime(declaration, self.global_env)
                )

    def load_imports(self, program, filename):
        if not program.imports:
            return

        if filename is None:
            raise RuntimeErrorLang(
                "No se pueden resolver imports sin conocer "
                "el archivo de origen."
            )

        base = Path(filename).resolve().parent

        for module in program.imports:
            candidates = [
                base / module,
                base / f"{module}.rl",
                base / f"{module}.rnl",
                base / f"{module}.src",
                base / f"{module}.fnt"
            ]

            path = next(
                (candidate.resolve() for candidate in candidates
                 if candidate.is_file()),
                None
            )

            if path is None:
                raise RuntimeErrorLang(
                    f"No se encontró el módulo: {module}"
                )

            self.load_file(path)

    def load_file(self, filename):
        path = Path(filename).resolve()

        if path in self.loaded_files:
            return

        if path in self.loading_files:
            raise RuntimeErrorLang(
                f"Importación circular detectada: {path.name}"
            )

        self.loading_files.add(path)

        try:
            source = path.read_text(encoding="utf-8")
            program = parse(source)

            self.load_imports(program, str(path))
            self.register_program(program)

            self.loaded_files.add(path)

        finally:
            self.loading_files.remove(path)

    def execute(self, source, filename=None, entry="main"):
        self.reset_execution()
        program = parse(source)

        if filename is not None:
            self.load_imports(program, filename)

        self.register_program(program)

        if entry is None:
            return None

        function = self.global_env.get_function(entry)

        if function is None:
            raise RuntimeErrorLang(
                f"No existe la función de entrada: {entry}"
            )

        return self.call_function(function, [])

    def execute_file(self, filename, entry="main"):
        self.reset_execution()
        path = Path(filename).resolve()
        self.load_file(path)

        if entry is None:
            return None

        function = self.global_env.get_function(entry)

        if function is None:
            raise RuntimeErrorLang(
                f"No existe la función de entrada: {entry}"
            )

        return self.call_function(function, [])

    def build_source(self, name):
        if name in self.source_instances:
            return self.source_instances[name]

        declaration = self.sources.get(name)

        if declaration is None:
            raise RuntimeErrorLang(
                f"Fuente desconocida: {name}"
            )

        env = Environment(kind="source")
        env.define("__type__", "function")
        runtime = SourceRuntime(declaration, env)
        self.source_instances[name] = runtime

        self.execute_source_body(declaration.body, runtime, env)

        return runtime

    def execute_source_body(self, body, runtime, env):
        for statement in body:
            if isinstance(statement, SourceDecl):
                self.sources[statement.name] = statement

            elif isinstance(statement, FunctionDecl):
                function = FunctionRuntime(statement, env)
                runtime.functions[statement.name] = function
                env.define_function(statement.name, function)

            elif isinstance(statement, IfStmt):
                if self.evaluate(statement.condition, env):
                    self.execute_source_body(statement.body, runtime, env)
                else:
                    for branch in statement.elif_branches:
                        if self.evaluate(branch.condition, env):
                            self.execute_source_body(
                                branch.body, runtime, env
                            )
                            break

            elif isinstance(statement, Assign):
                self.execute_assignment(statement, env)

            elif isinstance(statement, ExprStmt):
                expression = statement.expression

                if (
                    isinstance(expression, CallExpr)
                    and isinstance(expression.callee, Name)
                    and expression.callee.value == "expose"
                ):
                    if len(expression.arguments) != 1:
                        raise RuntimeErrorLang(
                            "expose() necesita exactamente un argumento."
                        )

                    specification = self.evaluate(
                        expression.arguments[0], env
                    )

                    if not isinstance(specification, str):
                        raise RuntimeErrorLang(
                            "expose() necesita un texto."
                        )

                    if specification.startswith("var:"):
                        variable_name = specification[4:].strip()

                        if not variable_name:
                            raise RuntimeErrorLang(
                                "Falta el nombre de la variable en expose()."
                            )

                        if variable_name not in env.values:
                            raise RuntimeErrorLang(
                                f"No existe la variable '{variable_name}' "
                                f"para exponer."
                            )

                        runtime.exposed_variables.add(variable_name)
                    else:
                        if specification not in runtime.functions:
                            raise RuntimeErrorLang(
                                f"No existe la función '{specification}' "
                                f"para exponer."
                            )

                        runtime.exposed.add(specification)

                else:
                    raise RuntimeErrorLang(
                        "Expresión no permitida en una fuente."
                    )

            else:
                raise RuntimeErrorLang(
                    "Declaración no permitida en una fuente."
                )

    def call_function(self, function, arguments):
        if isinstance(function, SourceFunction):
            function = function.runtime.functions.get(function.name)

        if not isinstance(function, FunctionRuntime):
            raise RuntimeErrorLang(
                "El objeto llamado no es una función."
            )

        declaration = function.declaration

        if len(arguments) != len(declaration.parameters):
            raise RuntimeErrorLang(
                f"{declaration.name} esperaba "
                f"{len(declaration.parameters)} argumentos, "
                f"pero recibió {len(arguments)}."
            )

        env = Environment(function.closure, kind="function")

        for name, value in zip(declaration.parameters, arguments):
            env.define(name, value)

        active_sources = {}

        for source_name in declaration.sources:
            runtime = self.build_source(source_name)
            active_sources[source_name] = runtime

            for exposed_name in runtime.exposed:
                if exposed_name in env.prefunctions:
                    previous = env.prefunctions[exposed_name]

                    if previous != source_name:
                        env.prefunctions[exposed_name] = None
                else:
                    env.prefunctions[exposed_name] = source_name

        env.define("__type__", "function")

        for source_name, runtime in active_sources.items():
            env.define(source_name, runtime)

        try:
            self.execute_block(declaration.body, env)
        except ReturnSignal as signal:
            return signal.value

        return None

    def execute_block(self, body, env):
        for statement in body:
            self.execute_statement(statement, env)

    def execute_assignment(self, statement, env):
        value = self.evaluate(statement.value, env)
        target = statement.target

        if isinstance(target, Variable):
            if target.scope == "local":
                if env.kind != "function":
                    raise RuntimeErrorLang(
                        "Las variables l! solo pueden utilizarse dentro de una función."
                    )
                env.local_values[target.name] = value
            elif target.scope == "program":
                self.program_env.define(target.name, value)
            else:
                raise RuntimeErrorLang("Ámbito de variable desconocido.")
            return

        if isinstance(target, Name):
            env.assign_source(target.value, value)
            return

        raise RuntimeErrorLang("Destino de asignación inválido.")

    def execute_statement(self, statement, env):
        if isinstance(statement, ReturnStmt):
            value = None

            if statement.value is not None:
                value = self.evaluate(statement.value, env)

            raise ReturnSignal(value)

        if isinstance(statement, IfStmt):
            if self.evaluate(statement.condition, env):
                self.execute_block(statement.body, env)
            else:
                for branch in statement.elif_branches:
                    if self.evaluate(branch.condition, env):
                        self.execute_block(branch.body, env)
                        break

            return

        if isinstance(statement, FunctionDecl):
            env.define_function(
                statement.name,
                FunctionRuntime(statement, env)
            )
            return

        if isinstance(statement, Assign):
            self.execute_assignment(statement, env)
            return

        if isinstance(statement, ExprStmt):
            self.evaluate(statement.expression, env)
            return

        raise RuntimeErrorLang(
            f"Instrucción desconocida: {type(statement).__name__}"
        )

    def evaluate(self, expression, env):
        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, Variable):
            if expression.scope == "local":
                if env.kind != "function":
                    raise RuntimeErrorLang(
                        "Las variables l! solo pueden utilizarse dentro de una función."
                    )
                return env.get_local(expression.name)

            if expression.scope == "program":
                if expression.name not in self.program_env.values:
                    raise RuntimeErrorLang(
                        f"Variable de programa desconocida: {expression.name}"
                    )
                return self.program_env.values[expression.name]

            raise RuntimeErrorLang("Ámbito de variable desconocido.")

        if isinstance(expression, Name):
            try:
                return env.get(expression.value)
            except RuntimeErrorLang:
                pass

            function = env.get_function(expression.value)

            if function is not None:
                return function

            if expression.value in env.prefunctions:
                source_name = env.prefunctions[expression.value]

                if source_name is None:
                    raise RuntimeErrorLang(
                        f"Nombre ambiguo: {expression.value}"
                    )

                runtime = self.build_source(source_name)

                return SourceFunction(
                    runtime,
                    expression.value
                )

            raise RuntimeErrorLang(
                f"Nombre desconocido: {expression.value}"
            )

        if isinstance(expression, Member):
            obj = self.evaluate(expression.object, env)

            if isinstance(obj, SourceRuntime):
                if expression.name in obj.exposed_variables:
                    return obj.env.get(expression.name)

                if expression.name not in obj.exposed:
                    raise RuntimeErrorLang(
                        f"La fuente no expone '{expression.name}'."
                    )

                return SourceFunction(obj, expression.name)

            raise RuntimeErrorLang(
                "No se puede acceder a ese miembro."
            )

        if isinstance(expression, CallExpr):
            if (
                isinstance(expression.callee, Name)
                and expression.callee.value == "expose"
            ):
                raise RuntimeErrorLang(
                    "expose() solo puede utilizarse dentro de una fuente."
                )

            if isinstance(expression.callee, Name):
                name = expression.callee.value
                function = env.get_function(name)

                if function is None and name in env.prefunctions:
                    source_name = env.prefunctions[name]

                    if source_name is None:
                        raise RuntimeErrorLang(
                            f"Nombre ambiguo: {name}"
                        )

                    runtime = self.build_source(source_name)
                    function = SourceFunction(runtime, name)

                if function is None:
                    raise RuntimeErrorLang(
                        f"Función desconocida: {name}"
                    )
            else:
                function = self.evaluate(expression.callee, env)

            arguments = [
                self.evaluate(argument, env)
                for argument in expression.arguments
            ]

            return self.call_function(function, arguments)

        if isinstance(expression, Unary):
            value = self.evaluate(expression.operand, env)

            if expression.operator == "!":
                return not value

            if expression.operator == "-":
                return -value

            if expression.operator == "+":
                return +value

        if isinstance(expression, Binary):
            left = self.evaluate(expression.left, env)

            if expression.operator == "&&":
                return bool(left) and bool(
                    self.evaluate(expression.right, env)
                )

            if expression.operator == "||":
                return bool(left) or bool(
                    self.evaluate(expression.right, env)
                )

            right = self.evaluate(expression.right, env)
            op = expression.operator

            operations = {
                "+": lambda: left + right,
                "-": lambda: left - right,
                "*": lambda: left * right,
                "/": lambda: left / right,
                "%": lambda: left % right,
                "==": lambda: left == right,
                "!=": lambda: left != right,
                "<": lambda: left < right,
                ">": lambda: left > right,
                "<=": lambda: left <= right,
                ">=": lambda: left >= right
            }

            if op not in operations:
                raise RuntimeErrorLang(
                    f"Operador desconocido: {op}"
                )

            try:
                return operations[op]()
            except Exception as error:
                raise RuntimeErrorLang(
                    f"Error al ejecutar '{op}': {error}"
                ) from error

        raise RuntimeErrorLang(
            f"Expresión desconocida: {type(expression).__name__}"
        )
