# SPDX-FileCopyrightText: 2024-present Abdelrahman Abdelrahman <me@abogic.al>
#
# SPDX-License-Identifier: MIT
"""Validate and impute your dataset with mathematical expressions.

Symbolic Constraints, or `symconstraints` for short, allows you to express your dataset rules
using mathematical equations and expressions. It makes use of the powerful `SymPy <https://www.sympy.org>`_ Computer Algebra System to analyze
mathematical expressions and infer all possible validation and imputation methods to your datasets. Helping you clean
your dataset with little code.

Examples
--------
TODO
"""

from symconstraints.constraints import Constraints
from symconstraints.operation import Operation, Validation, Imputation

__docformat__ = "numpy"
__all__ = ["Constraints", "Operation", "Validation", "Imputation"]
__version__ = "0.0.1"
