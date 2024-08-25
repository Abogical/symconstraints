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
from functools import cache, reduce
from itertools import combinations

from symconstraints import Constraints, Validation, Imputation
from sympy.logic.boolalg import Boolean
import numpy as np
from operator import or_


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


@cache
def _set_cover(subsets_buffer: bytes, shape: tuple[int, int]) -> list[int]:
    if shape[0] == 0 or shape[1] == 0:
        return []

    subsets = np.frombuffer(subsets_buffer, dtype=bool).reshape(shape)
    for symbol_amount in range(1, subsets.shape[1]):
        for selection in combinations(range(subsets.shape[1]), symbol_amount):
            if subsets[:, selection].any(axis=1).all():
                return list(selection)
    return list(range(subsets.shape[1]))


def set_invalid_min(
    check_result: pandas.DataFrame,
    df: pandas.DataFrame,
    fill=math.nan,
    priority: list[Symbol] | None = None,
) -> pandas.DataFrame:
    """Replace the minimum amount of possible invalid values in the dataframe to a set value.

    Similar to `set_invalid_all`, this replaces values in the dataframe that could possibly be invalid under the given constraints.
    However it does not replace all the values, instead it tries to replace the minimum amount of values in each row such that
    it satisfies all the constraints. This might help get rid of outlier data within the dataframe, while also keeping more of the values
    in the dataset unchanged.

    The input dataframe is copied and is not edited in-place.

    Parameters
    ----------
    check_result : pandas.DataFrame
        Check result returned by `check_result`
    df : pandas.DataFrame
        Dataframe to edit
    fill : Any, optional
        The set value to replace invalid values.
    priority : list[Symbol] | None, optional
        In case of a tie in the decision to set which column, refer to this priority to decide which
        column to to set first. Priority is ordered from most preferred to be set to least preferred.

    Returns
    -------
    pandas.DataFrame
        Dataframe with replaced values.

    Examples
    --------
    >>> import pandas as pd
    >>> from symconstraints import Constraints
    >>> from symconstraints.pandas import symbols, check, set_invalid_min
    >>> from sympy import Eq
    >>> df = pd.DataFrame(
    ...    {
    ...        "height": [5, 6, 8, 9, 7],
    ...        "width": [3, 5, 90, None, 8],
    ...        "depth": [None, 2, 10, 5, 5],
    ...        "area": [14, 30, 10, None, 35],
    ...        "volume": [None, 60, 100, 30, None],
    ...    },
    ...    dtype=float,
    ... )
    >>> height, width, area, depth, volume = symbols(df, ["height", "width", "area", "depth", "volume"])
    >>> constraints = Constraints([
    ...     Eq(area, height * width),
    ...     Eq(volume, area * depth),
    ...     height > width,
    ...     width > depth,
    ... ])
    >>> check_result = check(constraints, df)
    >>> set_invalid_min(check_result, df, priority=[volume, area, depth, width, height])
       height  width  depth  area  volume
    0     5.0    3.0    NaN   NaN     NaN
    1     6.0    5.0    2.0  30.0    60.0
    2     NaN   90.0   10.0   NaN   100.0
    3     9.0    NaN    5.0   NaN    30.0
    4     7.0    NaN    5.0   NaN     NaN
    """
    validation_sets = check_result.columns.get_level_values(0).unique()
    symbols = reduce(or_, validation_sets, frozenset())
    symbols_str = [str(s) for s in symbols]

    if priority is not None:
        priority_indices = dict(
            (str(value), index) for index, value in enumerate(priority)
        )
        symbols_str.sort(key=lambda symbol: priority_indices.get(symbol, math.inf))

    # Finding the minimum number of symbols to replace is equivalent to the set cover problem.
    check_sets = check_result.groupby(level=0, axis="columns").all()
    check_sets.columns = check_sets.columns.get_level_values(0)

    set_to_symbols = pandas.DataFrame(
        [
            dict(
                (symbol, symbol in frozenset(str(s) for s in subset))
                for symbol in symbols_str
            )
            for subset in validation_sets
        ],
        index=validation_sets,
    )

    set_cover_results = pandas.DataFrame(columns=[*validation_sets, *symbols_str])

    for _, selection in check_sets.drop_duplicates().iterrows():
        invalid_sets = selection.index[selection == 0.0]
        if not isinstance(invalid_sets, pandas.Index):
            raise ValueError(
                f"Unexpected value found when fetching invalid sets index: {invalid_sets}"
            )
        invalid_set_to_symbols = set_to_symbols.loc[invalid_sets, :]
        invalid_set_to_symbols = invalid_set_to_symbols[
            invalid_set_to_symbols.any(axis="columns")
        ]
        invalid_symbols = list(invalid_set_to_symbols.columns)
        invalid_set_to_symbols_numpy = invalid_set_to_symbols.to_numpy()
        symbols_to_remove = set(
            invalid_symbols[index]
            for index in _set_cover(
                invalid_set_to_symbols_numpy.tobytes(),
                invalid_set_to_symbols_numpy.shape,
            )
        )
        set_cover_results.loc[len(set_cover_results)] = pandas.concat(
            [
                selection,
                pandas.Series(
                    dict(
                        (symbol, symbol in symbols_to_remove) for symbol in symbols_str
                    )
                ),
            ]
        )

    to_set = check_sets.merge(set_cover_results, how="left")[symbols_str]
    to_set.index = check_sets.index  # I don't know why I have to do this.

    return df.where(~to_set, fill)


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
