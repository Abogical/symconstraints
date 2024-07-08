from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import TYPE_CHECKING

import sympy
from sympy import (
    And,
    Dummy,
    Eq,
    Basic,
    Ge,
    Gt,
    Interval,
    Le,
    Lt,
    Or,
    S,
    Symbol,
    oo,
    simplify_logic,
    solveset,
    FiniteSet,
    Expr,
)

if TYPE_CHECKING:
    from typing import Iterable, Literal

    from sympy.logic.boolalg import Boolean

from symconstraints.operation import Imputation, Validation

AllRelations = Eq | Le | Ge | Lt | Gt

_assumption_domain = {
    "real": S.Reals,
    "complex": S.Complexes,
    "integer": S.Integers,
    "negative": Interval(-oo, 0),
    "positive": Interval(0, oo),
}


def _get_symbol_domain(symbol):
    result = S.Complexes
    for assumption, is_assumption_true in symbol.assumptions0.items():
        domain = _assumption_domain.get(assumption)
        if domain is not None:
            result = (
                result.intersect(domain)
                if is_assumption_true
                else domain.complement(result)
            )
    return result


class _DummyRelation:
    rel: Literal["<", ">", "="]
    expr: Basic
    strict: bool

    def __init__(self, relation: AllRelations, dummy: Dummy):
        self.strict = isinstance(relation, (Lt, Gt))
        if isinstance(relation, Eq):
            self.rel = "="
            self.expr = relation.rhs if relation.lhs == dummy else relation.lhs
        elif relation.gts == dummy:
            self.rel = ">"
            self.expr = relation.lts
        else:
            self.rel = "<"
            self.expr = relation.gts


def _and_dummy_to_constraints(and_relation: And, dummy: Dummy) -> set[Boolean]:
    constraints: set[Boolean] = set()
    for relation1, relation2 in combinations(
        (
            _DummyRelation(rel, dummy)
            for rel in and_relation.args
            if isinstance(rel, AllRelations)
        ),
        2,
    ):
        match (relation1.rel, relation2.rel):
            case ("=", "="):
                constraints.add(Eq(relation1.expr, relation2.expr))
            case (">" | "=", "<" | "="):
                constraints.add(
                    (Lt if relation1.strict or relation2.strict else Le)(
                        relation1.expr, relation2.expr
                    )
                )
            case ("<" | "=", ">" | "="):
                constraints.add(
                    (Gt if relation1.strict or relation2.strict else Ge)(
                        relation1.expr, relation2.expr
                    )
                )

    return constraints


def _get_basic_symbols(basic: Basic):
    return frozenset(
        symbol for symbol in basic.free_symbols if isinstance(symbol, Symbol)
    )


class Constraints:
    _validations: list[Validation]
    _imputations: list[Imputation]

    def __init__(self, constraints: Iterable[Boolean]):
        symbol_to_sets: defaultdict[Symbol, set] = defaultdict(set)
        symbols_to_constraints: defaultdict[frozenset[Symbol], set] = defaultdict(set)
        self._imputations = []

        for constraint in constraints:
            symbols = _get_basic_symbols(constraint)
            symbols_to_constraints[symbols].add(constraint)
            for symbol in symbols:
                symbol_set = solveset(
                    constraint, symbol, domain=_get_symbol_domain(symbol)
                )
                symbol_to_sets[symbol].add(symbol_set)

                self._add_possible_imputation_from_set(symbol_set, symbol)

        for symbol, symbol_sets in symbol_to_sets.items():
            for set1, set2 in combinations(symbol_sets, 2):
                dummy = Dummy(**symbol.assumptions0)
                dummy_relation = simplify_logic(
                    set1.intersect(set2).as_relational(dummy), form="dnf"
                )
                if isinstance(dummy_relation, Or):
                    and_operations: list[Boolean] = []
                    for arg in dummy_relation.args:
                        if isinstance(arg, And):
                            and_operations += list(
                                _and_dummy_to_constraints(arg, dummy)
                            )
                        else:
                            and_operations = []
                            break
                    if len(and_operations) > 0:
                        constraint = Or(*and_operations)
                        symbols_to_constraints[_get_basic_symbols(constraint)].add(
                            constraint
                        )
                elif isinstance(dummy_relation, And):
                    for constraint in _and_dummy_to_constraints(dummy_relation, dummy):
                        constraint_symbols = _get_basic_symbols(constraint)
                        symbols_to_constraints[constraint_symbols].add(constraint)
                        for constraint_symbol in constraint_symbols:
                            constraint_symbol_set = solveset(
                                constraint, constraint_symbol
                            )
                            self._add_possible_imputation_from_set(
                                constraint_symbol_set, constraint_symbol
                            )

        self._validations = [
            Validation(frozenset(str(sym) for sym in symbols), frozenset(constraints))
            for symbols, constraints in symbols_to_constraints.items()
        ]

    def _add_possible_imputation_from_set(
        self, set_expr: sympy.Set, target_expr: Symbol
    ):
        if isinstance(set_expr, FiniteSet) and len(set_expr) == 1:
            expr = set_expr.args[0]
            if isinstance(expr, Expr):
                self._imputations.append(
                    Imputation(
                        frozenset(str(sym) for sym in _get_basic_symbols(expr)),
                        str(target_expr),
                        expr,
                    )
                )

    def get_validation_operations(self) -> list[Validation]:
        return self._validations

    def get_imputation_operations(self) -> list[Imputation]:
        return self._imputations
