"""Integration with [Pandas](https://pandas.pydata.org/) to aid in data cleaning dataframes."""

import pandas
import math
from sympy import Symbol, lambdify
from pandas.api.types import (
    is_unsigned_integer_dtype,
    is_integer_dtype,
    is_float_dtype,
    is_complex_dtype,
)
from functools import cache

from symconstraints import Constraints, Validation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sympy.logic.boolalg import Boolean


def symbols(
    df: pandas.DataFrame, columns: str | list[str], **kwargs
) -> Symbol | list[Symbol]:
    """Return SymPy symbols with assumptions inferred from the dataframe dtypes.

    Currently, it infers the following:

    * Unsigned integer dtypes are inferred to be nonnegative integers
    * Float dtypes are inferred to be real numbers
    * Complex dtypes are inferred to be complex numbers

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to infer symbol assumptions from.
    symbol_list : str | list[str]
        List of columns, can be represented as a space separated string.
    **kwargs: dict, optional
        Extra arguments to be passed to `sympy.Symbol`

    Returns
    -------
    Symbol | list[Symbol]
        SymPy symbols with assumptions inferred from the dataframe dtypes, corresponding to each column given.
        Returns a list if multiple columns are given, or a single symbol if a signle column is given.

    Raises
    ------
    ValueError
        Raises a ValueError if a column is not found or an unsupported dtype is found.

    Examples
    --------
    >>> import pandas as pd
    >>> from symconstraints.pandas import symbols
    >>> df = pd.DataFrame({
    ...    'Level': [1],
    ...    'Width': [5.3],
    ...    'Height': [7.6],
    ...    'Voltage': [5+3j]
    ... }).astype({'Level': 'uint8'})
    >>> level, width, voltage = symbols(df, 'Level Width Voltage')
    >>> level.is_nonnegative, level.is_integer
    (True, True)
    >>> width.is_integer, width.is_real
    (None, True)
    >>> voltage.is_real, voltage.is_complex
    (None, True)
    """
    result = []
    symbols = columns if isinstance(columns, list) else columns.split()
    for symbol in symbols:
        symbol_dtype = df.dtypes.get(symbol)
        if symbol_dtype is None:
            raise ValueError(
                f"Column {symbol} does not exist in the dataframe provided. Available columns are {list(df.columns)}."
            )

        assumptions = (
            {"integer": True, "nonnegative": True}
            if is_unsigned_integer_dtype(symbol_dtype)
            else {"integer": True}
            if is_integer_dtype(symbol_dtype)
            else {"real": True}
            if is_float_dtype(symbol_dtype)
            else {"complex": True}
            if is_complex_dtype(symbol_dtype)
            else None
        )

        if assumptions is None:
            raise ValueError(
                f"Unsupported data type {symbol_dtype} in column {symbol}."
            )

        result.append(Symbol(symbol, **assumptions, **kwargs))

    match len(result):
        case 0:
            raise ValueError("No symbols given.")
        case 1:
            return result[0]

    return result


@cache
def _lambdify(*args, **kwargs):
    return lambdify(*args, **kwargs, modules=["numpy"])


def check(
    constraints: Constraints | Validation, df: pandas.DataFrame
) -> pandas.DataFrame:
    """Return a table checking all the validations provided.

    Parameters
    ----------
    constraints : Constraints | Validation
        `Constraints` or `Validation` to use for checking.
    df : pandas.DataFrame
        Dataframe to check

    Returns
    -------
    pandas.DataFrame
        Returns a dataframe showing the result of all the validations for each row in the dataframe.
        Each column in the dataframe corresponds to each validation operation provided. Each row
        corresponds to each row in the original dataframe. A result of 1 is shown for successful validation,
        0 for an unsuccessful validation, and NaN for validations that can't be computed due to missing values.
        The result dtype is `float16`.

        If a `Constraints` object is provided, the columns are `pandas.MultiIndex`, where the top level is a set of
        columns with all validations concerning those sets of columns under it.

    Examples
    --------
    >>> import pandas as pd
    >>> from symconstraints.pandas import symbols, check
    >>> from symconstraints import Constraints
    >>> from sympy import Eq
    >>> df = pd.DataFrame({
    ...     'A': [5,6,8,9],
    ...     'B': [3,5,90,None],
    ...     'C': [14, 30, None, None]
    ... }, dtype=float)
    >>> A, B, C = symbols(df, ['A', 'B', 'C'])
    >>> constraints = Constraints([A > B, Eq(C, B*A)])
    >>> check(constraints, df)
    # Order may differ
      (A, B)  (C, A, B)  (C, B)  (C, A)
       A > B Eq(C, A*B) B < C/B A > C/A
    0    1.0        0.0     1.0     1.0
    1    1.0        1.0     1.0     1.0
    2    0.0        NaN     NaN     NaN
    3    NaN        NaN     NaN     NaN
    """
    if isinstance(constraints, Validation):
        columns = tuple(constraints.keys)
        index: list[Boolean] = list(constraints.operations)
        columns_str = [str(column) for column in columns]

        relevant_indices = ~df[columns_str].isna().any(axis="columns")
        if not isinstance(relevant_indices, pandas.Series):
            raise RuntimeError(
                f"unexpected type for relevant_indices: {type(relevant_indices)}"
            )

        relevant_df = df[relevant_indices]
        # Return a dataframe if the output is a series
        return pandas.DataFrame(
            pandas.concat(
                [
                    pandas.concat(
                        dict(
                            (
                                operation,
                                _lambdify(columns, operation)(
                                    *(relevant_df[str(column)] for column in columns)
                                ).astype("float16"),
                            )
                            for operation in index
                        ),
                        axis="columns",
                    ),
                    pandas.concat(
                        dict(
                            (
                                operation,
                                pandas.Series(
                                    math.nan,
                                    index=relevant_indices.index[~relevant_indices],
                                    copy=True,
                                ),
                            )
                            for operation in index
                        ),
                        axis="columns",
                    ),
                ],
                axis="rows",
            )
        )

    if isinstance(constraints, Constraints):
        return pandas.concat(
            dict(
                (validation.keys, check(validation, df))
                for validation in constraints.validations
            ),
            axis="columns",
        )

    raise ValueError(f"Invalid constraints given: {constraints}")
