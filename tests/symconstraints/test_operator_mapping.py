import pytest
from symconstraints import Validation, symbols, Constraints
from symconstraints.operator_mapping import (
    validate_mapping,
    ValidationError,
    ConstraintsValidationError,
)
from symconstraints import operator_mapping
import re
from ast import literal_eval
import unittest
import doctest


def test_validate_dict():
    a, b = symbols("a b")
    validation_op = a < b
    validation = Validation(frozenset([a, b]), frozenset([validation_op]))

    validate_mapping(validation, {"a": 5, "b": 8})

    invalid_input = {"a": 10, "b": 1}

    with pytest.raises(ValidationError) as invalid_result:
        validate_mapping(validation, invalid_input)

    assert len(invalid_result.value.unsatisfied_booleans) == 1
    assert invalid_result.value.unsatisfied_booleans[0] == validation_op
    assert invalid_result.value.values == invalid_input

    invalid_result_match = re.fullmatch(
        r"Mapping (\{[^}]*\}) is invalid due to not satisfying "
        + re.escape(f"[{validation_op}]"),
        str(invalid_result.value),
    )
    assert invalid_result_match is not None
    assert literal_eval(invalid_result_match.group(1)) == invalid_input


def test_validate_constraint():
    a, b, c = symbols("a b c")
    validation_ops = [a < b, b < c]

    constraints = Constraints(validation_ops)

    valid_input = {"a": 1, "b": 2, "c": 3}

    validate_mapping(constraints, valid_input)

    invalid_input = {"a": 1, "c": 0}

    with pytest.raises(ConstraintsValidationError) as invalid_result:
        validate_mapping(constraints, invalid_input)

    unsatisfied_validations = [
        validation_error for validation_error in invalid_result.value.validation_errors
    ]
    assert len(unsatisfied_validations) == 1
    assert unsatisfied_validations[0].unsatisfied_booleans == [a < c]

    assert (
        str(invalid_result.value)
        == f"Mapping is invalid due to:\n- {unsatisfied_validations[0]}"
    )


def test_wrong_validation():
    with pytest.raises(ValueError, match="Invalid constraints given: 33"):
        validate_mapping(33, {"a": 1, "b": 7})  # type: ignore


dict_re = re.compile(r"(\{[^}]*\})")


class OutputChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        # Don't care about exact order of output as it is not deterministic
        return dict_re.sub("", want) == dict_re.sub("", got) and all(
            literal_eval(want_obj) == literal_eval(got_obj)
            for want_obj, got_obj in zip(dict_re.findall(want), dict_re.findall(got))
        )


def test_docs():
    assert (
        unittest.TextTestRunner()
        .run(doctest.DocTestSuite(operator_mapping, checker=OutputChecker()))
        .wasSuccessful()
    )
