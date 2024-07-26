"""Integration with [Pandas](https://pandas.pydata.org/) to aid in data cleaning dataframes."""

import pandas
from sympy import Symbol
from pandas.api.types import (
    is_unsigned_integer_dtype,
    is_integer_dtype,
    is_float_dtype,
    is_complex_dtype,
)


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
