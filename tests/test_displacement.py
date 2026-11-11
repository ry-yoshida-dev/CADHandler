import pytest
from cartesian_axis import Axis
from units import LengthUnit, MetricPrefix

from cad_handler import AxialLength, Displacement

from .conftest import MM, offset_mm

MILLI = (LengthUnit.M, MetricPrefix.MILLI)


def test_missing_axes_are_zero() -> None:
    offset = Displacement.of(AxialLength(magnitude=4.0 * MM, axis=Axis.Y, is_negative=True))
    assert offset.signed_values(*MILLI) == pytest.approx((0.0, -4.0, 0.0))
    assert offset == offset_mm(0.0, -4.0, 0.0)


def test_along_returns_component() -> None:
    component = AxialLength(magnitude=1.0 * MM, axis=Axis.Z)
    assert Displacement.of(component).along(Axis.Z) == component


def test_rejects_duplicate_axes() -> None:
    with pytest.raises(ValueError, match="distinct axes"):
        Displacement.of(
            AxialLength(magnitude=1.0 * MM, axis=Axis.X),
            AxialLength(magnitude=2.0 * MM, axis=Axis.X),
        )


def test_addition_crosses_zero() -> None:
    total = offset_mm(1.0, 2.0, 0.0) + offset_mm(-3.0, 1.0, 0.0)
    assert total == offset_mm(-2.0, 3.0, 0.0)


def test_subtraction_and_negation() -> None:
    assert offset_mm(1.0, 1.0, 1.0) - offset_mm(1.0, 2.0, 3.0) == offset_mm(0.0, -1.0, -2.0)
    assert -offset_mm(1.0, -2.0, 0.0) == offset_mm(-1.0, 2.0, 0.0)
