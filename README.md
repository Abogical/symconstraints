# Symbolic Constraints

<!-- [![PyPI - Version](https://img.shields.io/pypi/v/symconstraints.svg)](https://pypi.org/project/symconstraints)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/symconstraints.svg)](https://pypi.org/project/symconstraints) -->

[![CI Test Status](https://img.shields.io/github/actions/workflow/status/abogical/symconstraints/tests.yaml?branch=main&label=tests&style=for-the-badge)](https://github.com/abogical/symconstraints/actions/workflows/ci-tests.yml?query=branch%3Amain)

Website: https://abogical.github.io/symconstraints/

-----
Validate and impute your dataset with mathematical expressions.

Symbolic Constraints, or `symconstraints` for short, allows you to express your dataset rules
using mathematical equations and expressions. It makes use of the powerful [SymPy](https://www.sympy.org) Computer Algebra System to analyze
mathematical expressions and infer all possible validation and imputation methods to your datasets. Helping you clean
your dataset with little code.

## Table of Contents

- [Installation](#installation)
- [Examples](#examples)
- [License](#license)

## Installation

This package is still a work in progress and not ready for release yet. A package will be published as soon as it is ready.

## Examples

### Validate and impute a Pandas Dataframe

```python
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
```

## License

`symconstraints` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
