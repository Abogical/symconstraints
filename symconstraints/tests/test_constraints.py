import random
from collections import defaultdict

from sympy import Eq, Le, Lt, S, solveset, sqrt
from sympy.logic.boolalg import Boolean

from symconstraints import Constraints, symbols, constraints
from symconstraints.operation import Validation, Imputation
import doctest
import unittest


def equal_bools(bool1: Boolean, bool2: Boolean, domain=S.Reals):
    symb1 = frozenset(bool1.free_symbols)
    symb2 = frozenset(bool2.free_symbols)
    if symb1 != symb2:
        return False

    if len(symb1) == 0:
        return bool1 == bool2

    pivot_symb = random.choice(list(symb1))
    return solveset(bool1, pivot_symb, domain=domain) == solveset(
        bool2, pivot_symb, domain=domain
    )


def check_validations(validations, correct_constraints):
    symbols_to_constraints = defaultdict(set)
    for constraint in correct_constraints:
        symbols_to_constraints[frozenset(constraint.free_symbols)].add(constraint)

    correct_validations = {
        Validation(frozenset(symbols), frozenset(constraints))
        for symbols, constraints in symbols_to_constraints.items()
    }

    unequal_validations1 = correct_validations - frozenset(validations)
    unequal_validations2 = set(validations) - correct_validations

    for validation1 in unequal_validations1:
        equal_validation = None
        for validation2 in unequal_validations2:
            if validation1.keys == validation2.keys and all(
                any(
                    equal_bools(constraint1, constraint2)
                    for constraint2 in validation2.operations
                )
                for constraint1 in validation1.operations
            ):
                equal_validation = validation2
                unequal_validations2.remove(validation2)
                break

        assert (
            equal_validation is not None
        ), f"No equivalent to {validation1} in {validations}"

    assert unequal_validations2 == set(), "Extra validations detected"


def test_inferred_equal_validations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, 2 * b), Eq(c, b + 3)])

    check_validations(
        constraints.get_validations(),
        [Eq(a, 2 * b), Eq(c, b + 3), Eq(c, a / 2 + 3)],
    )

    constraints = Constraints([Eq(a, b + c), Eq(c, d - e)])

    check_validations(
        constraints.get_validations(),
        [Eq(a, b + c), Eq(c, d - e), Eq(a, b + d - e)],
    )


def test_inferred_inequality_validations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, b + c), Le(c, d - e)])

    check_validations(
        constraints.get_validations(),
        [Eq(a, b + c), Le(c, d - e), Le(a, b + d - e)],
    )

    constraints = Constraints([Le(a, b + c), Le(c, d - e)])

    check_validations(
        constraints.get_validations(),
        [Le(a, b + c), Le(c, d - e), Le(a, b + d - e)],
    )


def test_inferred_inequality_strictness_validations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, b + c), Lt(c, d - e)])

    check_validations(
        constraints.get_validations(),
        [Eq(a, b + c), Lt(c, d - e), Lt(a, b + d - e)],
    )


def test_inferred_equal_imputations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, b + c), Eq(c, d - e)])

    assert frozenset(constraints.get_imputations()) == frozenset(
        [
            Imputation(frozenset([b, c]), a, b + c),
            Imputation(frozenset([a, c]), b, a - c),
            Imputation(frozenset([a, b]), c, a - b),
            Imputation(frozenset([d, e]), c, d - e),
            Imputation(frozenset([c, e]), d, c + e),
            Imputation(frozenset([c, d]), e, d - c),
            Imputation(frozenset([b, d, e]), a, b + d - e),
            Imputation(frozenset([a, d, e]), b, a - d + e),
            Imputation(frozenset([a, b, e]), d, a - b + e),
            Imputation(frozenset([a, b, d]), e, d - a + b),
        ]
    )


def test_inferred_square_equality_validations():
    a, b, c, d = symbols("a b c d", real=True)

    constraints = Constraints([Eq(a, 2 * b + d), Eq(c, b**2 + a**2)])

    check_validations(
        constraints.get_validations(),
        [
            Eq(a, 2 * b + d),
            Eq(c, b**2 + a**2),
            Eq(a / 2 - d / 2, sqrt(-(a**2) + c))
            | Eq(a / 2 - d / 2, -sqrt(-(a**2) + c)),
            Eq(2 * b + d, sqrt(-(b**2) + c)) | Eq(2 * b + d, -sqrt(-(b**2) + c)),
        ],
    )

class OutputChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        # Don't care about exact order of output as it is not deterministic
        return len(want.splitlines()) == len(got.splitlines()) and len(want) == len(got)

def test_docs():
    assert unittest.TextTestRunner().run(doctest.DocTestSuite(
        constraints,
        checker=OutputChecker()
    )).wasSuccessful()
