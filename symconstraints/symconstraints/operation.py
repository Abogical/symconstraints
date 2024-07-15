"""Operations module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sympy.logic.boolalg import Boolean
    from sympy import Expr


@dataclass(eq=True, frozen=True)
class Operation:
    """Generic operation.

    Attributes
    ----------
    keys : frozenset[str]
        Set of keys that this operation needs to check if its not missing before executing.
    """

    keys: frozenset[str]


@dataclass(eq=True, frozen=True)
class Validation(Operation):
    """Validation operation.

    Attributes
    ----------
    operations : frozenset[Boolean]
        A set of SymPy Boolean expressions that are used to validate the keys.
    """

    operations: frozenset[Boolean]

    def __str__(self):
        return f'Validation: ({", ".join(self.keys)}) => [{", ".join(str(op) for op in self.operations)}]'

    def __repr__(self):
        return str(self)


@dataclass(eq=True, frozen=True)
class Imputation(Operation):
    """Imputation operation.

    Attributes
    ----------
    target_key : str
        Key that will be imputed by this operation

    operation : Expr
        SymPy expression used to impute the target key
    """

    target_key: str
    operation: Expr

    def __str__(self):
        return f'Imputation: ({", ".join(self.keys)}) => {self.target_key} = {self.operation}'

    def __repr__(self):
        return str(self)
