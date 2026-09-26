"""
test_ast_analyzer.py – Tests for the Phase 1 AST analysis module.

Each test writes a temporary .py file, runs analyze_file() on it, and
checks the structured output.  No external dependencies are required.

Scenarios covered:
  1. Standalone functions
  2. Classes with methods
  3. Imports (bare and from-import)
  4. Decorators on functions and classes
  5. Nested functions inside a function
  6. Nested classes inside a class
  7. Syntax error – graceful handling, no crash
  8. Empty Python file
"""

import json
import sys
import textwrap
import tempfile
from pathlib import Path

# Allow running from the analysis directory directly
sys.path.insert(0, str(Path(__file__).parent))

from ast_analyzer import analyze_file  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_tmp(source: str) -> Path:
    """Write *source* to a temporary .py file and return its Path."""
    source = textwrap.dedent(source)
    tmp = tempfile.NamedTemporaryFile(suffix=".py", mode="w",
                                     encoding="utf-8", delete=False)
    tmp.write(source)
    tmp.close()
    return Path(tmp.name)


def run(source: str) -> dict:
    path = write_tmp(source)
    return analyze_file(path)


def heading(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def show(result: dict) -> None:
    print(json.dumps(result, indent=2))


PASS = "  PASS"
FAIL = "  FAIL"

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"{PASS}  {message}")
    else:
        print(f"{FAIL}  {message}")
        failures.append(message)


# ---------------------------------------------------------------------------
# Test 1 – Standalone functions
# ---------------------------------------------------------------------------

heading("Test 1 – Standalone functions")

result = run("""
    def greet(name):
        return f"Hello, {name}"

    def add(a, b):
        return a + b
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")
check(len(result["functions"]) == 2, "two top-level functions found")
check(result["functions"][0]["name"] == "greet", "first function is 'greet'")
check(result["functions"][1]["name"] == "add", "second function is 'add'")
check(result["functions"][0]["line_start"] == 2, "greet starts on line 2")
check(result["functions"][1]["line_start"] == 5, "add starts on line 5")
check(result["classes"] == [], "no classes")

# ---------------------------------------------------------------------------
# Test 2 – Classes with methods
# ---------------------------------------------------------------------------

heading("Test 2 – Classes with methods")

result = run("""
    class Animal:
        def __init__(self, name):
            self.name = name

        def speak(self):
            return "..."

    class Dog(Animal):
        def speak(self):
            return "Woof!"
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")
check(len(result["classes"]) == 2, "two classes found")
animal = result["classes"][0]
dog = result["classes"][1]
check(animal["name"] == "Animal", "first class is 'Animal'")
check(dog["name"] == "Dog", "second class is 'Dog'")
check(len(animal["methods"]) == 2, "Animal has 2 methods")
check(animal["methods"][0]["name"] == "__init__", "first method is '__init__'")
check(animal["methods"][1]["name"] == "speak", "second method is 'speak'")
check(len(dog["methods"]) == 1, "Dog has 1 method")
check(dog["methods"][0]["name"] == "speak", "Dog.speak found")

# ---------------------------------------------------------------------------
# Test 3 – Imports
# ---------------------------------------------------------------------------

heading("Test 3 – Imports")

result = run("""
    import os
    import os.path
    from pathlib import Path
    from typing import List, Optional
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")
check(len(result["imports"]) == 4, "four import records")

types = [i["type"] for i in result["imports"]]
check(types[0] == "import", "first is bare import")
check(types[1] == "import", "second is bare import")
check(types[2] == "from_import", "third is from-import")
check(types[3] == "from_import", "fourth is from-import")

check(result["imports"][0]["module"] == "os", "import os")
check(result["imports"][1]["module"] == "os.path", "import os.path")
check(result["imports"][2]["module"] == "pathlib", "from pathlib")
check(result["imports"][2]["names"] == ["Path"], "Path imported")
check(result["imports"][3]["names"] == ["List", "Optional"], "List, Optional imported")

# ---------------------------------------------------------------------------
# Test 4 – Decorators
# ---------------------------------------------------------------------------

heading("Test 4 – Decorators on functions and classes")

result = run("""
    import dataclasses

    def my_decorator(fn):
        return fn

    @my_decorator
    def plain():
        pass

    @my_decorator
    @staticmethod
    def double_decorated():
        pass

    @dataclasses.dataclass
    class Point:
        @staticmethod
        def origin():
            return Point()
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")

fns = {f["name"]: f for f in result["functions"]}
check("plain" in fns, "'plain' function found")
check(fns["plain"]["decorators"] == ["my_decorator"], "plain has @my_decorator")
check("double_decorated" in fns, "'double_decorated' found")
check(
    "my_decorator" in fns["double_decorated"]["decorators"]
    and "staticmethod" in fns["double_decorated"]["decorators"],
    "double_decorated has both decorators",
)

cls = result["classes"][0]
check(cls["name"] == "Point", "Point class found")
check("dataclasses.dataclass" in cls["decorators"], "Point has @dataclasses.dataclass")
check(cls["methods"][0]["decorators"] == ["staticmethod"], "origin has @staticmethod")

# ---------------------------------------------------------------------------
# Test 5 – Nested functions
# ---------------------------------------------------------------------------

heading("Test 5 – Nested functions")

result = run("""
    def outer():
        def inner():
            pass

        def another_inner():
            def deep():
                pass
        return inner
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")
outer = result["functions"][0]
check(outer["name"] == "outer", "outer function found")
check(len(outer["nested_functions"]) == 2, "outer has 2 nested functions")
check(outer["nested_functions"][0]["name"] == "inner", "first nested is 'inner'")
check(outer["nested_functions"][1]["name"] == "another_inner", "second nested is 'another_inner'")
another = outer["nested_functions"][1]
check(len(another["nested_functions"]) == 1, "another_inner has 1 nested function")
check(another["nested_functions"][0]["name"] == "deep", "deepest nested is 'deep'")

# ---------------------------------------------------------------------------
# Test 6 – Nested classes
# ---------------------------------------------------------------------------

heading("Test 6 – Nested classes")

result = run("""
    class Outer:
        class Inner:
            def inner_method(self):
                pass

        class AnotherInner:
            class DeepNested:
                pass
""")

show(result)

check(result["syntax_error"] is None, "no syntax error")
outer_cls = result["classes"][0]
check(outer_cls["name"] == "Outer", "Outer class found")
check(len(outer_cls["nested_classes"]) == 2, "Outer has 2 nested classes")
inner = outer_cls["nested_classes"][0]
check(inner["name"] == "Inner", "Inner class found")
check(inner["methods"][0]["name"] == "inner_method", "Inner.inner_method found")
another_inner = outer_cls["nested_classes"][1]
check(len(another_inner["nested_classes"]) == 1, "AnotherInner has 1 nested class")
check(another_inner["nested_classes"][0]["name"] == "DeepNested", "DeepNested found")

# ---------------------------------------------------------------------------
# Test 7 – Syntax error
# ---------------------------------------------------------------------------

heading("Test 7 – Syntax error (graceful handling)")

result = run("""
    def broken(
        # missing closing paren and colon
""")

show(result)

check(result["syntax_error"] is not None, "syntax_error is populated")
check(isinstance(result["syntax_error"], str), "syntax_error is a string")
check(result["imports"] == [], "imports list is empty on parse failure")
check(result["functions"] == [], "functions list is empty on parse failure")
check(result["classes"] == [], "classes list is empty on parse failure")
print(f"  syntax_error message: {result['syntax_error']!r}")

# ---------------------------------------------------------------------------
# Test 8 – Empty file
# ---------------------------------------------------------------------------

heading("Test 8 – Empty file")

result = run("")

show(result)

check(result["syntax_error"] is None, "no syntax error on empty file")
check(result["line_count"] == 0, "line_count is 0 for empty file")
check(result["imports"] == [], "no imports")
check(result["functions"] == [], "no functions")
check(result["classes"] == [], "no classes")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

heading("Summary")
total_checks = sum(1 for line in open(__file__, encoding="utf-8")
                   if "check(" in line)

if failures:
    print(f"\n  {len(failures)} FAILURE(S):")
    for f in failures:
        print(f"    - {f}")
    sys.exit(1)
else:
    print(f"\n  All checks passed!")
    sys.exit(0)
