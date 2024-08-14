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

from symconstraints import Constraints, Validation, Imputation
from sympy.logic.boolalg import Boolean


def symbols(
    df: pandas.DataFrame, symbol_list: str | list[str], **kwargs
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
    symbols = symbol_list if isinstance(symbol_list, list) else symbol_list.split()
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


def set_invalid_all(
    check_result: pandas.DataFrame, df: pandas.DataFrame, fill=math.nan
) -> pandas.DataFrame:
    """Replace all possible invalid values in the dataframe to a set value.

    This replaces values in the dataframe that could possibly be invalid under the given constraints. This might help
    get rid of outlier data within the dataframe.

    The input dataframe is copied and is not edited in-place.

    Parameters
    ----------
    check_result : pandas.DataFrame
        Check result returned by `check_result`
    df : pandas.DataFrame
        Dataframe to edit
    fill : Any, optional
        The set value to replace invalid values.

    Returns
    -------
    pandas.DataFrame
        Dataframe with replaced values.

    Examples
    --------
    >>> import pandas as pd
    >>> from symconstraints import Constraints
    >>> from symconstraints.pandas import symbols, check, set_invalid_all
    >>> from sympy import Eq
    >>> df = pd.DataFrame(
    ...    {
    ...         "height": [5, 6, 8, 9],
    ...         "width": [3, 5, 90, None],
    ...         "area": [14, 30, None, 18],
    ...     },
    ...     dtype=float,
    ... )
    >>> height, width, area = symbols(df, ["height", "width", "area"])
    >>> constraints = Constraints([height > width, Eq(area, width * height)])
    >>> check_result = check(constraints, df)
    >>> set_invalid_all(check_result, df)
       height  width  area
    0     NaN    NaN   NaN
    1     6.0    5.0  30.0
    2     NaN    NaN   NaN
    3     9.0    NaN  18.0
    """
    result = df.copy()
    if check_result.empty:
        return result
    if check_result.columns.nlevels == 1:
        column_item = check_result.columns.item()
        if not isinstance(column_item, Boolean):
            raise ValueError(
                f"Invalid check result given. It has a column {column_item} of type: {type(column_item)}"
            )
        result.loc[
            ~check_result.fillna(1.0).all(axis="columns"),
            [str(symbol) for symbol in column_item.free_symbols],
        ] = fill

        return result

    keysets = check_result.columns.get_level_values(0)

    invalid_keysets = [keys for keys in keysets if not isinstance(keys, frozenset)]
    if len(invalid_keysets) > 0:
        raise ValueError(f"Found invalid columns in check result: {invalid_keysets}")

    for keys in keysets:
        result.loc[
            ~check_result[keys].fillna(1.0).all(axis="columns"),
            [str(key) for key in keys],
        ] = fill

    return result


def impute(
    constraints: Constraints | Imputation, df: pandas.DataFrame
) -> pandas.DataFrame:
    """Impute the dataframe under the given constraints.

    This returns a copy of the dataframe with all NA values replaced with values inferred from
    imputation operations given in the constraints. This assumes that all the values are valid,
    so it is recommended that the dataframe be checked and that all of its invalid values are
    removed via `check` and `set_invalid_all`.

    The input dataframe is not edited in-place.

    Parameters
    ----------
    constraints : Constraints | Imputation
        `Constraints` or `Imputation` to use for imputation.
    df : pandas.DataFrame
        Dataframe to impute.

    Returns
    -------
    pandas.DataFrame
        Imputed dataframe.

    Examples
    --------
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
    if isinstance(constraints, Imputation):
        result = df.copy()

        columns = tuple(constraints.keys)
        columns_str = [str(column) for column in columns]

        result.loc[
            result[columns_str].notna().all(axis="columns")
            & result[str(constraints.target_key)].isna(),
            str(constraints.target_key),
        ] = _lambdify(columns, constraints.operation)(
            *(result[column_str] for column_str in columns_str)
        )

        return result

    if isinstance(constraints, Constraints):
        result = df.copy()

        for imputation in constraints.imputations:
            columns = tuple(imputation.keys)
            columns_str = [str(column) for column in columns]

            result.loc[
                result[columns_str].notna().all(axis="columns")
                & result[str(imputation.target_key)].isna(),
                str(imputation.target_key),
            ] = _lambdify(columns, imputation.operation)(
                *(result[column_str] for column_str in columns_str)
            )

        return result

    raise ValueError(f"Invalid constraints given: {constraints}")
