# SPDX-FileCopyrightText: 2024-present Abdelrahman Abdelrahman <me@abogic.al>
#
# SPDX-License-Identifier: MIT
"""Validate and impute your dataset with mathematical expressions.

Symbolic Constraints, or `symconstraints` for short, allows you to express your dataset rules
using mathematical equations and expressions. It makes use of the powerful [SymPy](https://www.sympy.org) Computer Algebra System to analyze
mathematical expressions and infer all possible validation and imputation methods to your datasets. Helping you clean
your dataset with little code.

Examples
--------
Validate and impute a dataframe
>>> import pandas as pd
>>> from symconstraints import Constraints
>>> from symconstraints.pandas import symbols, check, set_invalid_all, impute
>>> from sympy import Eq
>>> df = pd.DataFrame(
...    {
...         "height": [5, 6, 8, 9],
...         "width": [3, 5, 7, None],
...         "area": [14, 30, None, 18],
...     },
...     dtype=float,
... )
>>> height, width, area = symbols(df, ["height", "width", "area"])
>>> constraints = Constraints([height > width, Eq(area, width * height)])
>>> check_result = check(constraints, df)
>>> df = set_invalid_all(check_result, df)
>>> df
    height  width  area
0     NaN    NaN   NaN
1     6.0    5.0  30.0
2     8.0    7.0   NaN
3     9.0    NaN  18.0
>>> imputed_df = impute(constraints, df)
>>> imputed_df
    height  width  area
0     NaN    NaN   NaN
1     6.0    5.0  30.0
2     8.0    7.0  56.0
3     9.0    2.0  18.0
"""

from symconstraints.constraints import Constraints, symbols
from symconstraints.operation import Operation, Validation, Imputation

__docformat__ = "numpy"
__all__ = ["Constraints", "symbols", "Operation", "Validation", "Imputation"]
__version__ = "0.0.1"
