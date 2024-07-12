from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sympy.logic.boolalg import Boolean
    from sympy import Expr


@dataclass(eq=True, frozen=True)
class Operation:
    columns: frozenset[str]


@dataclass(eq=True, frozen=True)
class Validation(Operation):
    operations: frozenset[Boolean]

    def __str__(self):
        return f'Validation: ({", ".join(self.columns)}) => [{", ".join(str(op) for op in self.operations)}]'


@dataclass(eq=True, frozen=True)
class Imputation(Operation):
    target_column: str
    operation: Expr

    def __str__(self):
        return f'Imputation: ({", ".join(self.columns)}) => {self.target_column} = {self.operation}'
