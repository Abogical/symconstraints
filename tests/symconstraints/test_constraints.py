import random
from collections import defaultdict

from sympy import Eq, Le, Lt, S, solveset, sqrt, Or, Union
from sympy.logic.boolalg import Boolean

from symconstraints import Constraints, symbols, constraints
from symconstraints.operation import Validation, Imputation
import doctest
import unittest


def extended_solveset(expr: Boolean, *args, **kwargs):
    if isinstance(expr, Or):
        return Union(*(solveset(arg, *args, **kwargs) for arg in expr.args))
    return solveset(expr, *args, **kwargs)


def equal_bools(bool1: Boolean, bool2: Boolean, domain=S.Reals):
    symb1 = frozenset(bool1.free_symbols)
    symb2 = frozenset(bool2.free_symbols)
    if symb1 != symb2:
        return False

    if len(symb1) == 0:
        return bool1 == bool2

    pivot_symb = random.choice(list(symb1))

    return extended_solveset(bool1, pivot_symb, domain=domain) == extended_solveset(
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
        constraints.validations,
        [Eq(a, 2 * b), Eq(c, b + 3), Eq(c, a / 2 + 3)],
    )

    constraints = Constraints([Eq(a, b + c), Eq(c, d - e)])

    check_validations(
        constraints.validations,
        [Eq(a, b + c), Eq(c, d - e), Eq(a, b + d - e)],
    )


def test_inferred_inequality_validations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, b + c), Le(c, d - e)])

    check_validations(
        constraints.validations,
        [Eq(a, b + c), Le(c, d - e), Le(a, b + d - e)],
    )

    constraints = Constraints([Le(a, b + c), Le(c, d - e)])

    check_validations(
        constraints.validations,
        [Le(a, b + c), Le(c, d - e), Le(a, b + d - e)],
    )


def test_inferred_inequality_strictness_validations():
    a, b, c, d, e = symbols("a b c d e")

    constraints = Constraints([Eq(a, b + c), Lt(c, d - e)])

    check_validations(
        constraints.validations,
        [Eq(a, b + c), Lt(c, d - e), Lt(a, b + d - e)],
    )


def test_inferred_equal_imputations():
    a, b, c, d, e = symbols("a b c d e")

    constraint1 = Eq(a, b + c)
    constraint2 = Eq(c, d - e)
    constraints = Constraints([constraint1, constraint2])

    assert frozenset(constraints.imputations) == frozenset(
        [
            Imputation(
                frozenset([b, c]), a, b + c, inferred_by=frozenset([constraint1])
            ),
            Imputation(
                frozenset([a, c]), b, a - c, inferred_by=frozenset([constraint1])
            ),
            Imputation(
                frozenset([a, b]), c, a - b, inferred_by=frozenset([constraint1])
            ),
            Imputation(
                frozenset([d, e]), c, d - e, inferred_by=frozenset([constraint2])
            ),
            Imputation(
                frozenset([c, e]), d, c + e, inferred_by=frozenset([constraint2])
            ),
            Imputation(
                frozenset([c, d]), e, d - c, inferred_by=frozenset([constraint2])
            ),
            Imputation(
                frozenset([b, d, e]),
                a,
                b + d - e,
                inferred_by=frozenset([constraint1, constraint2]),
            ),
            Imputation(
                frozenset([a, d, e]),
                b,
                a - d + e,
                inferred_by=frozenset([constraint1, constraint2]),
            ),
            Imputation(
                frozenset([a, b, e]),
                d,
                a - b + e,
                inferred_by=frozenset([constraint1, constraint2]),
            ),
            Imputation(
                frozenset([a, b, d]),
                e,
                d - a + b,
                inferred_by=frozenset([constraint1, constraint2]),
            ),
        ]
    )


def test_inferred_square_equality_validations():
    a, b, c, d = symbols("a b c d", real=True)

    constraints = Constraints([Eq(a, 2 * b + d), Eq(c, b**2 + a**2)])

    check_validations(
        constraints.validations,
        [
            Eq(a, 2 * b + d),
            Eq(c, b**2 + a**2),
            Eq(a / 2 - d / 2, sqrt(-(a**2) + c))
            | Eq(a / 2 - d / 2, -sqrt(-(a**2) + c)),
            Eq(2 * b + d, sqrt(-(b**2) + c)) | Eq(2 * b + d, -sqrt(-(b**2) + c)),
        ],
    )


def test_square_inequality_validations():
    a, b, c, d = symbols("a b c d", real=True)

    constraint1 = a**2 > 5
    constraint2 = Eq(a + b, 8)
    constraints = Constraints([constraint1, constraint2])

    check_validations(
        constraints.validations,
        [constraint1, constraint2, (8 - b) ** 2 > 5],
    )

    assert frozenset(constraints.imputations) == frozenset(
        [
            Imputation(frozenset([b]), a, 8 - b, inferred_by=frozenset([constraint2])),
            Imputation(frozenset([a]), b, 8 - a, inferred_by=frozenset([constraint2])),
        ]
    )

    constraints = Constraints([Eq(a, 2 * b + d), c < (b**2 + a)])

    check_validations(
        constraints.validations,
        [
            Eq(a, 2 * b + d),
            c < (b**2 + a),
            2 * b + d > c - b**2,
            ((a - d) / 2 > sqrt(c - a)) | ((a - d) / 2 < -sqrt(c - a)),
        ],
    )

    constraint1 = Eq(a, 2 * b + d)
    constraint2 = c > (b**2 + a)
    constraints = Constraints([constraint1, constraint2])

    check_validations(
        constraints.validations,
        [
            constraint1,
            constraint2,
            2 * b + d < c - b**2,
            (a - d) / 2 > -sqrt(c - a),
            (a - d) / 2 < sqrt(c - a),
        ],
    )

    assert frozenset(constraints.imputations) == frozenset(
        [
            Imputation(
                frozenset([b, d]), a, 2 * b + d, inferred_by=frozenset([constraint1])
            ),
            Imputation(
                frozenset([a, d]), b, (a - d) / 2, inferred_by=frozenset([constraint1])
            ),
            Imputation(
                frozenset([a, b]), d, a - 2 * b, inferred_by=frozenset([constraint1])
            ),
        ]
    )


class OutputChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        # Don't care about exact order of output as it is not deterministic
        return len(want.splitlines()) == len(got.splitlines()) and len(want) == len(got)


def test_docs():
    assert (
        unittest.TextTestRunner()
        .run(doctest.DocTestSuite(constraints, checker=OutputChecker()))
        .wasSuccessful()
    )
