from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import TYPE_CHECKING

import sympy
from sympy import And, Dummy, Eq, Expr, Ge, Gt, Interval, Le, Lt, Or, S, Symbol, oo, simplify_logic, solveset

if TYPE_CHECKING:
    from typing import Iterable, Literal, Mapping

    from sympy.logic.boolalg import Boolean

from symconstraints.operation import Imputation, Validation

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
            result = result.intersect(domain) if is_assumption_true else domain.complement(result)
    return result


class _DummyRelation:
    rel: Literal["<", ">", "="]
    expr: Expr
    strict: bool

    def __init__(self, relation: sympy.core.relational.Relational, dummy: Dummy):
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


def _and_dummy_to_constraints(and_relation: And, dummy: Dummy):
    constraints: set[Boolean] = set()
    for relation1, relation2 in combinations((_DummyRelation(rel, dummy) for rel in and_relation.args), 2):
        match (relation1.rel, relation2.rel):
            case ("=", "="):
                constraints.add(Eq(relation1.expr, relation2.expr))
            case (">" | "=", "<" | "="):
                constraints.add((Lt if relation1.strict or relation2.strict else Le)(relation1.expr, relation2.expr))
            case ("<" | "=", ">" | "="):
                constraints.add((Gt if relation1.strict or relation2.strict else Ge)(relation1.expr, relation2.expr))

    return constraints


class Constraints:
    _validations: list[Validation]
    _imputations: list[Imputation]

    def __init__(self, constraints: Iterable[Boolean]):
        symbol_to_sets: Mapping[Symbol, sympy.Set] = defaultdict(set)
        symbols_to_constraints: Mapping[frozenset[Symbol], Constraints] = defaultdict(set)

        for constraint in constraints:
            symbols_to_constraints[frozenset(constraint.free_symbols)].add(constraint)
            for symbol in constraint.free_symbols:
                symbol_to_sets[symbol].add(solveset(constraint, symbol, domain=_get_symbol_domain(symbol)))

        for symbol, symbol_sets in symbol_to_sets.items():
            for set1, set2 in combinations(symbol_sets, 2):
                dummy = Dummy(**symbol.assumptions0)
                dummy_relation = simplify_logic(set1.intersect(set2).as_relational(dummy), form="dnf")
                if isinstance(dummy_relation, Or):
                    if all(isinstance(arg, And) for arg in dummy_relation.args):
                        and_operations = []
                        for arg in dummy_relation.args:
                            and_operations += list(_and_dummy_to_constraints(arg, dummy))

                    constraint = Or(*and_operations)
                    symbols_to_constraints[frozenset(constraint.free_symbols)].add(constraint)
                elif isinstance(dummy_relation, And):
                    for constraint in _and_dummy_to_constraints(dummy_relation, dummy):
                        symbols_to_constraints[frozenset(constraint.free_symbols)].add(constraint)

        self._validations = [
            Validation(frozenset(str(sym) for sym in symbols), frozenset(constraints))
            for symbols, constraints in symbols_to_constraints.items()
        ]

    def get_validation_operations(self) -> list[Validation]:
        return self._validations

    def get_imputation_operations(self) -> list[Imputation]:
        return self._imputations
