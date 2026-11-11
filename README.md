# Source
## Guía de uso del lenguaje

Source es un lenguaje de programación interpretado. Su sintaxis utiliza fuentes, funciones, variables y expresiones. Los bloques se delimitan con llaves `{ }`, mientras que algunas estructuras utilizan indentación.

La idea principal de Source es que "Todo tiene un origen" (o fuente).

Esta guía describe las características reconocidas por el lexer, el parser y el intérprete actuales.

## Información adicional

| Detalle | Información |
|---|---|
| Versión | 0.8 |
| Autor | Randommatix |

## Ejecutar Source

Desde donde este `main.py`, puedes ejecutar:

``` bash
python main.py programa.fnt
```

Reemplaza `programa.fnt` por el nombre real del archivo.

## Licencia

Source está distribuido bajo la licencia Apache License 2.0.
Consulta el archivo [LICENSE](LICENSE) para obtener más información.

---

## 1. Estructura de un programa

Un programa puede contener fuentes y funciones.

La función de entrada predeterminada es `main()`.

```c
* main() {
    return 10
}
```

Al ejecutar el programa, el intérprete busca `main()` y la llama automáticamente.

Si la función no existe, se produce un error indicando que no se encontró la función de entrada.

## 2. Funciones

Las funciones se declaran utilizando `*` seguido de su nombre y sus parámetros.

```c
* saludar() {
    return "Hola"
}
```

También pueden recibir parámetros:

```c
* sumar(a, b) {
    return a + b
}
```

Para llamar a una función se escribe su nombre seguido de paréntesis:

```c
* main() {
    resultado = sumar(5, 3)
    return resultado
}
```

La cantidad de argumentos debe coincidir con la cantidad de parámetros declarados.

Las funciones pueden devolver valores mediante `return`. Si se utiliza `return` sin una expresión, la función devuelve `None`.

## 3. Fuentes

Una fuente es una estructura que agrupa variables y funciones.

Se declara utilizando `*`, el nombre de la fuente y un bloque entre llaves.

```c
* calculadora {
    valor = 10

    * duplicar() {
        return valor * 2
    }
    expose("duplicar")
}
```

Las funciones de una fuente pueden compartir sus variables.

Para utilizar una fuente desde una función, se declara su asociación:

```c
calculadora main() {
    return duplicar()
}
```

También se pueden asociar varias fuentes:

```c
(calculadora, matematicas) main() {
    return duplicar()
}
```

Una función puede acceder a las funciones y variables que su fuente haya expuesto.

## 4. Variables

Source admite diferentes ámbitos de variables.

### Variables normales

Se crean mediante una asignación:

```c
dato = 25
```

Si la variable ya existe en el ámbito correspondiente, se actualiza. Si no existe, se crea.

Dentro de una fuente, las variables normales pueden compartirse entre sus funciones:

```c
* contador {
    valor = 0

    * incrementar() {
        valor = valor + 1
        return valor
    }
}
```

### Variables locales: `l!`

Las variables locales pertenecen a una invocación de función.

```c
* incrementar() {
    l!contador = 0
    l!contador = l!contador + 1
    return l!contador
}
```

El prefijo `l!` debe escribirse tanto al asignar como al leer la variable.

Cada llamada a la función obtiene su propio almacenamiento local. Por eso, `l!contador` comienza nuevamente en `0` en cada invocación.

Estas variables solamente pueden utilizarse dentro de funciones.

### Variables del programa: `o!`

Las variables con el prefijo `o!` pertenecen al programa y pueden compartirse entre sus funciones.

```c
* primera() {
    o!contador = 10
}

* segunda() {
    o!contador = o!contador + 5
    return o!contador
}
```

Al igual que con `l!`, el prefijo `o!` debe escribirse en cada referencia.

Las variables de programa no pertenecen a una fuente y no pueden exponerse mediante `expose()`.

### Variables con el mismo nombre

Los distintos ámbitos permiten utilizar el mismo nombre sin que las variables sean la misma.

```c
* ejemplo() {
    valor = 10
    l!valor = 20
    o!valor = 30
}
```

En este ejemplo existen tres variables diferentes.

## 5. Exponer elementos de una fuente

Por defecto, los elementos internos de una fuente no están disponibles para las funciones que la utilizan.

La función especial `expose()` permite hacer públicos determinados elementos.

Para exponer una función:

```c
* herramientas {
    * saludar() {
        return "Hola"
    }

    expose("saludar")
}
```

Para exponer una variable:

```c
* configuracion {
    velocidad = 5

    expose("var: velocidad")
}
```

Después de asociar la fuente a una función, se puede acceder a los elementos expuestos mediante el nombre de la fuente y el operador `.`.

```c
(configuracion) main() {
    return configuracion.velocidad
}
```

También se puede llamar a una función expuesta mediante el mismo mecanismo:

```c
(herramientas) main() {
    return herramientas.saludar()
}
```

`expose()` solamente puede utilizarse dentro de una fuente.

Para exponer una variable, esta debe existir previamente. Las variables `l!` y `o!` no pueden exponerse.

## 6. Condicionales

Source permite utilizar `if` y `elif`.

Los bloques condicionales utilizan `:` y se delimitan mediante indentación.

```c
* comprobar(valor) {
    if valor > 10:
        return true
    elif valor == 10:
        return false

    return false
}
```

La indentación es importante: define dónde comienza y termina cada bloque.

Actualmente, el parser reconoce `if` y `elif`; no implementa una rama `else`.

## 7. Operadores

### Aritméticos

| Operador | Operación |
|---|---|
| `+` | Suma |
| `-` | Resta |
| `*` | Multiplicación |
| `/` | División |
| `%` | Módulo |

### Comparación

| Operador | Operación |
|---|---|
| `==` | Igual |
| `!=` | Distinto |
| `<` | Menor |
| `>` | Mayor |
| `<=` | Menor o igual |
| `>=` | Mayor o igual |

### Lógicos

| Operador | Operación |
|---|---|
| `&&` | AND lógico |
| `||` | OR lógico |
| `!` | NOT lógico |

Los operadores `&&` y `||` utilizan evaluación de cortocircuito.

### Prioridad

La prioridad de los operadores, de mayor a menor, es:

1. Operadores unarios: `!`, `-`, `+`.
2. Multiplicación, división y módulo.
3. Suma y resta.
4. Comparaciones e igualdad.
5. AND lógico.
6. OR lógico.

Se pueden utilizar paréntesis para agrupar expresiones.

## 8. Tipos de valores

El lexer reconoce:

- Números enteros: `123`
- Números decimales: `12.5`
- Cadenas de texto: `"Hola"` o `'Hola'`
- Booleanos: `true` y `false`

Las cadenas admiten secuencias de escape:

| Secuencia | Significado |
|---|---|
| `\n` | Salto de línea |
| `\t` | Tabulación |
| `\r` | Retorno de carro |
| `\\` | Barra invertida |
| `\"` | Comilla doble |
| `\'` | Comilla simple |

Los valores pueden utilizarse en expresiones, asignaciones, condiciones y retornos.

## 9. Importar módulos

Source permite importar otros archivos mediante la directiva `#!import`.

```c
#!import "herramientas.src"

* main() {
    return calcular()
}
```

También se puede escribir el nombre del módulo sin comillas:

```c
#!import herramientas
```

El intérprete busca el archivo en el directorio del archivo que realiza la importación. Prueba el nombre indicado y las extensiones `.rl`, `.rnl`, `.src`, y `.fnt`.

Los módulos se cargan una sola vez durante la ejecución. El intérprete también detecta las importaciones circulares.

## 10. Comentarios

Los comentarios comienzan con `//`.

```c
// Este es un comentario

* main() {
    // Se ejecuta el programa
    return 1
}
```

El contenido posterior a `//` en una línea no se interpreta como código.

## 11. Errores

Source distingue errores de análisis y errores de ejecución.

Algunos ejemplos:

- Utilizar una variable que no existe.
- Llamar a una función desconocida.
- Llamar a una función con una cantidad incorrecta de argumentos.
- Intentar utilizar `expose()` fuera de una fuente.
- Acceder a un elemento que una fuente no expuso.
- Utilizar `l!` fuera de una función.
- Utilizar una fuente que no existe.
- Escribir una expresión o estructura que el parser no reconoce.

Los errores de sintaxis pueden incluir la línea y la columna donde se detectó el problema.

---

## 12. Bibliotecas estándar

Source incluye bibliotecas estándar que proporcionan funcionalidades comunes. Se importan mediante `#!import` y se utilizan asociando la fuente correspondiente a una función.

### 12.1. Biblioteca `string`

Proporciona utilidades para el manejo de cadenas de texto.

**Funciones expuestas:**

| Función | Descripción |
|---|---|
| `str(n)` | Convierte un número `n` a su representación como cadena de texto. |
| `len(s)` | Devuelve la longitud de la cadena `s`. |

**Ejemplo de uso:**

```c
#!import string

strings main() {
  return len("Hola")
}
```

Este programa devuelve `4`, la longitud de la cadena `"Hola"`.

### 12.2. Biblioteca `math`

Proporciona operaciones matemáticas básicas.

**Funciones expuestas:**

| Función | Descripción |
|---|---|
| `sumar(a, b)` | Devuelve la suma de `a` y `b`. |
| `cuadrado(a)` | Devuelve el cuadrado de `a`. |
| `promedio(a, b)` | Devuelve el promedio de `a` y `b`. |
| `porcentaje(valor, porcentaje)` | Devuelve el `porcentaje`% de `valor`. |
| `cubo(a)` | Devuelve el cubo de `a`. |

**Ejemplo de uso:**

```c
#!import math

math main() {
  return cubo(3)
}
```

Este programa devuelve `27`, el cubo de `3`.

### 12.3. Biblioteca `random`

Proporciona funciones para generar números pseudoaleatorios. Depende de la biblioteca `string`.

**Funciones expuestas:**

| Función | Descripción |
|---|---|
| `starts(representation)` | Inicializa la semilla (`seed`) a partir de la representación textual de un objeto. Extrae la dirección hexadecimal contenida en `representation` y la usa como semilla. Devuelve la semilla calculada. |
| `randint(a, b)` | Devuelve un número entero pseudoaleatorio en el rango cerrado `[a, b]`. Actualiza la semilla interna en cada llamada. |

**Variable expuesta:**

| Variable | Descripción |
|---|---|
| `seed` | Semilla actual del generador pseudoaleatorio. Puede leerse y modificarse externamente. |

**Ejemplo de uso:**

```c
#!import random

random main() {
    random.starts("%s" % random)
    return random.randint(1, 8) * 10
}
```

Este programa inicializa la semilla a partir de la representación de la propia fuente `random`, genera un número entero entre `1` y `8` y lo multiplica por `10`.

Para inicializar el generador, utiliza esta expresión:

`random.starts("%s" % random)`

Esto permite obtener una dirección hexadecimal de la representación
del objeto `random`, que se utiliza para inicializar la semilla.

Es necesario ejecutar esta instrucción porque la biblioteca no puede
obtener esa representación hexadecimal por sí sola.

---

## 13. Ejemplo completo

Este programa combina fuentes, variables, funciones, exposición y condicionales.

```c
* calculadora {
    resultado = 0

    * sumar(valor) {
        resultado = resultado + valor
        return resultado
    }

    expose("sumar")
    expose("var: resultado")
}

calculadora main() {
    l!primero = calculadora.sumar(10)
    l!segundo = calculadora.sumar(5)

    if l!segundo > l!primero:
        return calculadora.resultado
    elif l!segundo == l!primero:
        return 0

    return -1
}
```

La fuente `calculadora` mantiene su variable `resultado` compartida. La función `main()` utiliza dos variables locales independientes y accede a los elementos públicos de la fuente.

---

**Nota sobre la implementación:** esta guía describe las capacidades presentes en la versión del intérprete, lexer y parser utilizada como referencia. No presupone la existencia de ciclos, clases, arrays, funciones anónimas, entrada/salida integrada ni otras características que no aparecen implementadas en esos componentes.
