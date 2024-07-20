"""Basic implementations of operations to the standard python mapping (dict, defaultdict, etc.)."""

from sympy.logic.boolalg import Boolean
from symconstraints import Validation, Constraints
from dataclasses import dataclass

from collections.abc import Mapping
from typing import TypeVar, overload

AnyValueMap = Mapping[str, TypeVar("V")]


@dataclass(frozen=True)
class ValidationResult:
    """Validation result.

    Attributes
    ----------
    values
        Mapping values relevant to the validation operations.

    unsatisfied_booleans : list[Boolean]
        List of equalities/inequalities where these values do not satisfy.
    """

    values: AnyValueMap
    unsatisfied_booleans: list[Boolean]

    def __str__(self):
        return (
            "Mapping is valid"
            if len(self.unsatisfied_booleans) == 0
            else f"Mapping {self.values} is invalid due to not satisfying [{', '.join(str(op) for op in self.unsatisfied_booleans)}]"
        )

    def __bool__(self):
        return len(self.unsatisfied_booleans) == 0


@dataclass(frozen=True)
class ConstraintsValidationResult:
    """Constraints validation result.

    Attributes
    ----------
    validation_results : list[ValidationResult]
        List of results for each validations in the constraints.
    """

    validation_results: list[ValidationResult]

    def __bool__(self):
        return all(self.validation_results)

    def __str__(self):
        return (
            "Mapping is valid"
            if bool(self)
            else "Mapping is invalid due to:"
            + "".join(
                f"\n- {validation_result}"
                for validation_result in self.validation_results
                if not validation_result
            )
        )


@overload
def validate_mapping(
    constraints: Validation, input_dict: AnyValueMap
) -> ValidationResult: ...
@overload
def validate_mapping(
    constraints: Constraints, input_dict: AnyValueMap
) -> ConstraintsValidationResult: ...
def validate_mapping(constraints, input_dict: AnyValueMap):
    """Validate mapping via a validation or constraints.

    Parameters
    ----------
    constraints : Constraints | Validation
        Constraints or validation to use for validation.
    input_dict : AnyValueMap
        Input to validate

    Returns
    -------
    ConstraintsValidationResult | ValidationResult
        Returns a `ConstraintsValidationResult` when `symconstraints.Constraints` is given, or returns a
        `ValidationResult` when `symconstraints.Validation` is given as constraints.

    Raises
    ------
    ValueError
        Raised when an invalid constraints object is given.
    """
    if isinstance(constraints, Validation):
        values = dict((str(k), input_dict.get(str(k))) for k in constraints.keys)

        if any(input_dict.get(str(key)) is None for key in constraints.keys):
            return ValidationResult(values, [])

        values_subs = [(k, input_dict[str(k)]) for k in constraints.keys]

        return ValidationResult(
            values,
            [
                operation
                for operation in constraints.operations
                if not operation.subs(values_subs)
            ],
        )
    elif isinstance(constraints, Constraints):
        return ConstraintsValidationResult(
            [
                validate_mapping(validation, input_dict)
                for validation in constraints.get_validations()
            ]
        )
    else:
        raise ValueError(f"Invalid constraints given: {constraints}")
