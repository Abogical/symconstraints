from symconstraints import pandas as sympd
from symconstraints import Constraints, Validation
from sympy import Eq
import pandas as pd
import unittest
import doctest
import math
from collections import Counter


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


def test_check():
    df = pd.DataFrame(
        {
            "height": [5, 6, 8, 9],
            "width": [3, 5, 90, None],
            "area": [14, 30, None, None],
        },
        dtype=float,
    )

    symbols = sympd.symbols(df, ["height", "width", "area"])
    assert isinstance(symbols, list)
    height, width, area = symbols

    validation = Validation(frozenset([height, width]), frozenset([height > width]))

    check_result = sympd.check(validation, df)
    check_comparision = check_result.compare(
        pd.DataFrame({(height > width): [1.0, 1.0, 0.0, math.nan]}, dtype="float16")
    )

    assert check_comparision.empty, check_comparision

    constraints = Constraints([height > width, Eq(area, width * height)])

    check_result = sympd.check(constraints, df)
    assert len(check_result.columns) == 4
    check_comparision = check_result.compare(
        pd.DataFrame(
            pd.DataFrame(
                {
                    (frozenset([height, width]), (height > width)): [
                        1.0,
                        1.0,
                        0.0,
                        math.nan,
                    ],
                    (frozenset([area, height, width]), Eq(area, width * height)): [
                        0.0,
                        1.0,
                        math.nan,
                        math.nan,
                    ],
                    (frozenset([width, area]), width < area / width): [
                        1.0,
                        1.0,
                        math.nan,
                        math.nan,
                    ],
                    (frozenset([height, area]), height > area / height): [
                        1.0,
                        1.0,
                        math.nan,
                        math.nan,
                    ],
                },
                dtype="float16",
            )[check_result.columns]
        )
    )

    assert check_comparision.empty, check_comparision


class OutputChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        # Don't care about exact order of output as it is not deterministic
        want_lines, got_lines = list(want.splitlines()), list(got.splitlines())
        if len(want_lines) > 0 and "Order may differ" in want_lines[0]:
            del want_lines[0]
            return all(
                Counter(want_line) == Counter(got_line)
                for want_line, got_line in zip(want_lines, got_lines)
            )

        return super().check_output(want, got, optionflags)


def test_docs():
    assert (
        unittest.TextTestRunner()
        .run(doctest.DocTestSuite(sympd, checker=OutputChecker()))
        .wasSuccessful()
    )
