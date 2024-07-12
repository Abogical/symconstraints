from sympy import symbols, Eq, Le
from symconstraints.operation import Validation, Imputation
import re

validation_re = re.compile(r"Validation: \(([^\)]*)\) => \[([^\]]*)\]")


def check_validation_str(cols, ops):
    validation = Validation(frozenset(cols), frozenset(ops))
    match = validation_re.fullmatch(str(validation))
    assert match is not None
    assert frozenset(var.strip() for var in match.group(1).split(",")) == frozenset(
        cols
    )
    assert match.group(2) == ", ".join(str(op) for op in frozenset(ops))
    assert str(validation) == repr(validation)


def test_validation_str():
    a, b = symbols("a b")

    check_validation_str(["a", "b"], [Eq(a + b, 3)])
    check_validation_str(["a", "b"], [Le(a / 2, 3), Eq(b, a + 2)])


imputation_re = re.compile(r"Imputation: \(([^\)]*)\) => (\w+) = (.*)")


def check_imputation_str(cols, target, expr):
    imputation = Imputation(frozenset(cols), target, expr)
    match = imputation_re.fullmatch(str(imputation))
    assert match is not None
    assert frozenset(var.strip() for var in match.group(1).split(",")) == frozenset(
        cols
    )
    assert match.group(2) == str(target)
    assert match.group(3) == str(expr)
    assert str(imputation) == repr(imputation)


def test_imputation_str():
    a, b, c = symbols("a b c")

    check_imputation_str(["a", "b", "c"], a, b + c)
    check_imputation_str(["a", "b", "c"], b, 2 * a - c)
