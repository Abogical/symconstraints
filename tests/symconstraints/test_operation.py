from sympy import symbols, Eq, Le
from symconstraints.operation import Validation, Imputation
import re

validation_re = re.compile(r"Validation: \(([^\)]*)\) => \[([^\]]*)\] inferred by (.*)")


def check_validation_str(cols, ops, inferred_by):
    validation = Validation(
        frozenset(cols), frozenset(ops), inferred_by=frozenset(inferred_by)
    )
    match = validation_re.fullmatch(str(validation))
    assert match is not None
    assert frozenset(var.strip() for var in match.group(1).split(",")) == frozenset(
        cols
    )
    assert match.group(2) == ", ".join(str(op) for op in frozenset(ops))
    assert all(str(i) in match.group(3) for i in inferred_by)
    assert str(validation) == repr(validation)


def test_validation_str():
    a, b = symbols("a b")

    check_validation_str(["a", "b"], [Eq(a + b, 3)], [Eq(a, b - 3)])
    check_validation_str(
        ["a", "b"], [Le(a / b, 3), Eq(b, a + 2)], [a < 3 * b, Eq(a - 2, b)]
    )


imputation_re = re.compile(r"Imputation: \(([^\)]*)\) => (\w+) = (.*)")


def check_imputation_str(cols, target, expr, inferred_by):
    imputation = Imputation(
        frozenset(cols), target, expr, inferred_by=frozenset(inferred_by)
    )
    match = imputation_re.fullmatch(str(imputation))
    assert match is not None
    assert frozenset(var.strip() for var in match.group(1).split(",")) == frozenset(
        str(c) for c in cols
    )
    assert match.group(2) == str(target)
    expr_str, inferred_by_str = match.group(3).split("inferred by")
    assert expr_str.strip() == str(expr)
    assert all(str(i) in inferred_by_str for i in inferred_by)
    assert str(imputation) == repr(imputation)


def test_imputation_str():
    a, b, c = symbols("a b c")

    check_imputation_str([b, c], a, b + c, [Eq(a - b, c)])
    check_imputation_str([a, c], b, 2 * a - c, [Eq(c + b, 2 * a)])
