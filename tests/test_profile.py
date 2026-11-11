import numpy as np
import pytest
from units import Length, LengthUnit, MetricPrefix

from cad_handler import Profile

from .conftest import AUTOCAD, MM


def square(center: float, half_size: float) -> np.ndarray[tuple[int, int], np.dtype[np.float64]]:
    low, high = center - half_size, center + half_size
    return np.array([[low, low], [high, low], [high, high], [low, high]])


def test_nesting_depths_follow_containment() -> None:
    outer, hole, island = square(0.0, 10.0), square(0.0, 6.0), square(0.0, 2.0)
    side = square(30.0, 1.0)
    profile = Profile(
        loops=(island, outer, side, hole), coordinate_unit=MM, coordinate_system=AUTOCAD
    )
    assert profile.nesting_depths == (2, 0, 0, 1)


def test_loops_in_converts_coordinates() -> None:
    inch = Length(value=np.array([1.0]), unit=LengthUnit.INCH)
    profile = Profile(loops=(square(1.0, 1.0),), coordinate_unit=inch, coordinate_system=AUTOCAD)
    (loop,) = profile.loops_in(LengthUnit.M, MetricPrefix.MILLI)
    np.testing.assert_allclose(loop[2], [50.8, 50.8])


def test_rejects_empty_profile() -> None:
    with pytest.raises(ValueError, match="at least one loop"):
        Profile(loops=(), coordinate_unit=MM, coordinate_system=AUTOCAD)


@pytest.mark.parametrize(
    "loop",
    [np.zeros((2, 2)), np.zeros((4, 3)), np.array([[0.0, 0.0], [1.0, np.nan], [1.0, 1.0]])],
    ids=["too-few-vertices", "three-columns", "non-finite"],
)
def test_rejects_invalid_loop(loop: np.ndarray[tuple[int, int], np.dtype[np.float64]]) -> None:
    with pytest.raises(ValueError, match="Loop 0"):
        Profile(loops=(loop,), coordinate_unit=MM, coordinate_system=AUTOCAD)


def test_rejects_zero_coordinate_unit() -> None:
    with pytest.raises(ValueError, match="coordinate_unit"):
        Profile(loops=(square(0.0, 1.0),), coordinate_unit=0.0 * MM, coordinate_system=AUTOCAD)
