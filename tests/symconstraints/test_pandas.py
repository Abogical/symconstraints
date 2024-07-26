from symconstraints import pandas as sympd
import pandas as pd
import unittest
import doctest


def test_symbols():
    df = pd.DataFrame(
        {"a": [6, 7], "bg": [7.8, 5.5], "rr": [-5, 8], "comp": [5 + 1j, 7]}
    ).astype({"a": "uint8"})

    symbols = sympd.symbols(df, "a bg rr comp")
    assert isinstance(symbols, list)
    a, bg, rr, comp = symbols
    assert a.is_integer and a.is_nonnegative  # type: ignore
    assert bg.is_integer is None and bg.is_real  # type: ignore
    assert rr.is_integer and rr.is_nonnegative is None  # type: ignore
    assert comp.is_complex  # type: ignore

    assert sympd.symbols(df, "a bg rr comp") == sympd.symbols(
        df, ["a", "bg", "rr", "comp"]
    )


def test_docs():
    assert unittest.TextTestRunner().run(doctest.DocTestSuite(sympd)).wasSuccessful()
