from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sympy.logic.boolalg import Boolean


@dataclass(eq=True, frozen=True)
class Operation:
    columns: frozenset[str]


@dataclass(eq=True, frozen=True)
class Validation(Operation):
    operations: frozenset[Boolean]


@dataclass(eq=True, frozen=True)
class Imputation(Operation):
    target_column: str
    operations: frozenset
