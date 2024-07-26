"""Basic implementations of operations to the standard python mapping (dict, defaultdict, etc.)."""

from sympy.logic.boolalg import Boolean
from symconstraints import Validation, Constraints, Imputation

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


def impute_mapping(
    constraints: Imputation | Constraints, mapping: StringMap
) -> dict[str, Any]:
    """Impute mapping via a validation or constraints object.

    Parameters
    ----------
    constraints : Imputation | Constraints
        Constraints or Imputation object to use for imputation.
    mapping : StringMap
        Input to impute.

    Returns
    -------
    dict[str, Any]
        The imputed mapping as a dictionary.

    Examples
    --------
    >>> from sympy import Eq
    >>> from symconstraints import symbols, Constraints
    >>> from symconstraints.operator_mapping import impute_mapping
    >>> a, b, c, d = symbols("a b c d")
    >>> constraints = Constraints([Eq(a, 2 * b + c), c < b, Eq(d, a * c)])
    >>> impute_mapping(constraints, {"b": 10, "c": 3})
    {'a': 23, 'b': 10, 'c': 3, 'd': 69}
    """
    if isinstance(constraints, Imputation):
        if mapping.get(str(constraints.target_key)) is None and all(
            mapping.get(str(key)) is not None for key in constraints.keys
        ):
            return {
                **mapping,
                str(constraints.target_key): constraints.operation.subs(
                    [(key, mapping[str(key)]) for key in constraints.keys]
                ),
            }
        return dict(mapping)
    elif isinstance(constraints, Constraints):
        result = {**mapping}
        for imputation in constraints.imputations:
            result = impute_mapping(imputation, result)
        return result
    else:
        raise ValueError(f"Invalid constraints given: {constraints}")
