"""Basic implementations of operations to the standard python mapping (dict, defaultdict, etc.)."""

from sympy.logic.boolalg import Boolean
from symconstraints import Validation, Constraints

from collections.abc import Mapping
from typing import Any

StringMap = Mapping[str, Any]
"""Any generic map that has a string key, such as dict, defaultdict, Counter, etc."""


class ValidationError(Exception):
    """Validation error.

    Attributes
    ----------
    values
        Mapping values relevant to the validation operations.

    unsatisfied_booleans : list[Boolean]
        List of equalities/inequalities where these values do not satisfy.
    """

    values: StringMap
    unsatisfied_booleans: list[Boolean]

    def __init__(self, values: StringMap, unsatisfied_booleans: list[Boolean]):
        super().__init__(
            f"Mapping {values} is invalid due to not satisfying [{', '.join(str(op) for op in unsatisfied_booleans)}]"
        )

        self.values = values
        self.unsatisfied_booleans = unsatisfied_booleans


class ConstraintsValidationError(Exception):
    """Constraints validation error.

    Attributes
    ----------
    validation_errors : list[ValidationError]
        List of errors for each validations in the constraints.
    """

    validation_errors: list[ValidationError]

    def __init__(self, validation_errors: list[ValidationError]):
        super().__init__(
            "Mapping is invalid due to:"
            + "".join(
                f"\n- {validation_error}" for validation_error in validation_errors
            )
        )

        self.validation_errors = validation_errors


def validate_mapping(constraints: Constraints | Validation, mapping: StringMap):
    """Validate mapping via a validation or constraints.

    Parameters
    ----------
    constraints : Constraints | Validation
        Constraints or validation to use for validation.
    mapping : AnyValueMap
        Input to validate

    Raises
    ------
    ValueError
        Raised when an invalid constraints object is given.
    ValidationError
        Raised when the mapping data given is invalid under constraints of type `Validation`
    ConstraintsValidationError
        Raised when the mapping data given is invalid under constraints of type `Constraints`

    Examples
    --------
    >>> from symconstraints import Constraints, symbols
    >>> from symconstraints.operator_mapping import validate_mapping
    >>> a, b, c = symbols('a b c')
    >>> constraints = Constraints([a < b, b < c])
    >>> validate_mapping(constraints, {'a': 1, 'b': 2})
    >>> # Nothing happens, data is valid
    >>> try:
    ...   validate_mapping(constraints, {'a': 4, 'c': 1})
    ... except ConstraintsValidationError as e:
    ...   print(e)
    Mapping is invalid due to:
    - Mapping {'a': 4, 'c': 1} is invalid due to not satisfying [a < c]
    """
    if isinstance(constraints, Validation):
        values = dict((str(k), mapping.get(str(k))) for k in constraints.keys)

        if any(mapping.get(str(key)) is None for key in constraints.keys):
            return

        values_subs = [(k, mapping[str(k)]) for k in constraints.keys]

        unsatisfied_expressions: list[Boolean] = [
            operation
            for operation in constraints.operations
            if not operation.subs(values_subs)
        ]

        if len(unsatisfied_expressions) > 0:
            raise ValidationError(
                values,
                unsatisfied_expressions,
            )
    elif isinstance(constraints, Constraints):
        errors: list[ValidationError] = []
        for validation in constraints.validations:
            try:
                validate_mapping(validation, mapping)
            except ValidationError as e:
                errors.append(e)

        if len(errors) > 0:
            raise ConstraintsValidationError(errors)
    else:
        raise ValueError(f"Invalid constraints given: {constraints}")
