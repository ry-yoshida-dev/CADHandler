import math

import numpy as np
import pytest
from cartesian_axis import Axis
from units import Length, LengthUnit, MetricPrefix

from cad_handler import AxialLength

from .conftest import MM


def test_signed_value_follows_direction() -> None:
    forward = AxialLength(magnitude=5.0 * MM, axis=Axis.X)
    backward = AxialLength(magnitude=5.0 * MM, axis=Axis.X, is_negative=True)
    assert forward.signed_value(LengthUnit.M, MetricPrefix.MILLI) == pytest.approx(5.0)
    assert backward.signed_value(LengthUnit.M) == pytest.approx(-0.005)


def test_from_signed_value_keeps_unit_and_splits_sign() -> None:
    length = AxialLength.from_signed_value(-3.0, LengthUnit.INCH, Axis.Y)
    assert length.is_negative
    assert length.magnitude.unit is LengthUnit.INCH
    assert length.signed_value(LengthUnit.M, MetricPrefix.MILLI) == pytest.approx(-76.2)


def test_negation_reverses_direction() -> None:
    length = AxialLength(magnitude=2.0 * MM, axis=Axis.Z)
    reversed_length = -length
    assert reversed_length.is_negative
    assert -reversed_length == length


def test_equality_compares_across_units() -> None:
    in_millimeters = AxialLength(magnitude=10.0 * MM, axis=Axis.X)
    centi = Length(value=np.array([1.0]), unit=LengthUnit.M, prefix=MetricPrefix.CENTI)
    assert in_millimeters == AxialLength(magnitude=centi, axis=Axis.X)
    assert in_millimeters != AxialLength(magnitude=centi, axis=Axis.Y)
    assert in_millimeters != -in_millimeters


def test_zero_has_no_direction() -> None:
    zero = AxialLength(magnitude=0.0 * MM, axis=Axis.X)
    assert zero == -zero


@pytest.mark.parametrize(
    "values", [np.array([1.0, 2.0]), np.array([math.inf])], ids=["multiple", "infinite"]
)
def test_rejects_invalid_magnitude(values: np.ndarray[tuple[int], np.dtype[np.float64]]) -> None:
    with pytest.raises(ValueError, match="magnitude"):
        AxialLength(magnitude=Length(value=values, unit=LengthUnit.M), axis=Axis.X)


def test_from_signed_value_rejects_nan() -> None:
    with pytest.raises(ValueError, match="magnitude"):
        AxialLength.from_signed_value(math.nan, LengthUnit.M, Axis.X)
