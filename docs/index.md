# Symbolic Constraints

[![CI Test Status](https://img.shields.io/github/actions/workflow/status/abogical/symconstraints/tests.yaml?branch=main&label=tests&style=for-the-badge)](https://github.com/Abogical/symconstraints/actions/workflows/tests.yaml?query=branch%3Amain)

Validate and impute your dataset with mathematical expressions.

Symbolic Constraints, or `symconstraints` for short, allows you to express your dataset rules
using mathematical equations and expressions. It makes use of the powerful [SymPy](https://www.sympy.org) Computer Algebra System to analyze
mathematical expressions and infer all possible validation and imputation methods to your datasets.

## Features

### :fontawesome-solid-wand-magic-sparkles: Automatic inference

`symconstraints` uses SymPy to rearrange your formulas and find new ways to validate and impute your data.

!!! example

    ```python
    >>> from symconstraints import Constraints, symbols
    >>> a, b, c = symbols('a b c')
    >>> constraints = Constraints([a < 3*b, c > b**2 + 1])
    >>> for validation in constraints.validations
    ...     print(validation)
    Validation: (b, a) => [a < 3*b] inferred by (a < 3*b)
    Validation: (b, c) => [c > b**2 + 1] inferred by (c > b**2 + 1)
    Validation: (a, c) => [a/3 < sqrt(c - 1)] inferred by (c > b**2 + 1, a < 3*b)
    ```

    It automatically infers that $\frac{a}{3} < \sqrt{c-1}$.

### :fontawesome-solid-puzzle-piece: Integrations

Integrates with popular data science tools such as [Pandas](https://pandas.pydata.org/). Saving you time to help you clean your datasets with little code.

!!! example
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

 _scikit-learn and Pandera integrations are currently under development._

## License

`symconstraints` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
