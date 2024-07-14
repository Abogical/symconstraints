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
    columns : frozenset[str]
        Set of columns that this operation needs to check if its not missing before executing.
    """

    columns: frozenset[str]


@dataclass(eq=True, frozen=True)
class Validation(Operation):
    """Validation operation.

    Attributes
    ----------
    operations : frozenset[Boolean]
        A set of SymPy Boolean expressions that are used to validate the columns.
    """

    operations: frozenset[Boolean]

    def __str__(self):
        return f'Validation: ({", ".join(self.columns)}) => [{", ".join(str(op) for op in self.operations)}]'

    def __repr__(self):
        return str(self)


@dataclass(eq=True, frozen=True)
class Imputation(Operation):
    """Imputation operation.

    Attributes
    ----------
    target_column : str
        Column that will be imputed by this operation

    operation : Expr
        SymPy expression used to impute the target column
    """

    target_column: str
    operation: Expr

    def __str__(self):
        return f'Imputation: ({", ".join(self.columns)}) => {self.target_column} = {self.operation}'

    def __repr__(self):
        return str(self)
