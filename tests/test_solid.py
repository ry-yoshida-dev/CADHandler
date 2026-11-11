import math

import pytest
from cartesian_axis import Axis

from cad_handler import CADBackend, EmptySolidError, Modeler, Solid

from .conftest import AUTOCAD, DEGREE, assert_box_close, cube_mm, offset_mm


def test_union_covers_both(modeler: Modeler[Solid]) -> None:
    first = cube_mm(modeler, 1.0, 1.0, 1.0)
    second = cube_mm(modeler, 1.0, 1.0, 1.0).translate(offset_mm(2.0, 0.0, 0.0))
    assert_box_close(first.union(second).bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 1.0))
    assert_box_close((first | second).bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 1.0))


def test_difference_cuts_away(modeler: Modeler[Solid]) -> None:
    base = cube_mm(modeler, 4.0, 1.0, 1.0)
    cutter = cube_mm(modeler, 2.0, 3.0, 3.0).translate(offset_mm(2.0, -1.0, -1.0))
    assert_box_close(base.difference(cutter).bounding_box, (0.0, 0.0, 0.0), (2.0, 1.0, 1.0))
    assert_box_close((base - cutter).bounding_box, (0.0, 0.0, 0.0), (2.0, 1.0, 1.0))


def test_intersection_keeps_overlap(modeler: Modeler[Solid]) -> None:
    first = cube_mm(modeler, 2.0, 2.0, 2.0)
    second = cube_mm(modeler, 2.0, 2.0, 2.0).translate(offset_mm(1.0, 1.0, 1.0))
    assert_box_close(first.intersection(second).bounding_box, (1.0, 1.0, 1.0), (2.0, 2.0, 2.0))
    assert_box_close((first & second).bounding_box, (1.0, 1.0, 1.0), (2.0, 2.0, 2.0))


def test_full_difference_is_empty(modeler: Modeler[Solid]) -> None:
    box = cube_mm(modeler, 1.0, 1.0, 1.0)
    with pytest.raises(EmptySolidError):
        _ = (box - box).bounding_box


def test_operations_leave_receiver_unchanged(modeler: Modeler[Solid]) -> None:
    box = cube_mm(modeler, 1.0, 1.0, 1.0)
    box.translate(offset_mm(5.0, 5.0, 5.0)).rotate(Axis.Z, 45.0 * DEGREE).scale((2.0, 2.0, 2.0))
    _ = box | cube_mm(modeler, 1.0, 1.0, 1.0).translate(offset_mm(3.0, 0.0, 0.0))
    assert_box_close(box.bounding_box, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))


def test_translate(modeler: Modeler[Solid]) -> None:
    moved = cube_mm(modeler, 1.0, 2.0, 3.0).translate(offset_mm(1.0, -2.0, 3.0))
    assert_box_close(moved.bounding_box, (1.0, -2.0, 3.0), (2.0, 0.0, 6.0))


def test_chained_rotations_apply_in_call_order(modeler: Modeler[Solid]) -> None:
    rotated = (
        cube_mm(modeler, 1.0, 2.0, 3.0).rotate(Axis.X, 90.0 * DEGREE).rotate(Axis.Z, 90.0 * DEGREE)
    )
    assert_box_close(rotated.bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 2.0))


def test_rotate_about_z_is_counterclockwise(modeler: Modeler[Solid]) -> None:
    rotated = cube_mm(modeler, 1.0, 2.0, 3.0).rotate(Axis.Z, 90.0 * DEGREE)
    assert_box_close(rotated.bounding_box, (-2.0, 0.0, 0.0), (0.0, 1.0, 3.0))


@pytest.mark.parametrize(
    ("factors", "maximum"),
    [((2.0, 2.0, 2.0), (2.0, 2.0, 2.0)), ((2.0, 3.0, 4.0), (2.0, 3.0, 4.0))],
    ids=["uniform", "per-axis"],
)
def test_scale(
    modeler: Modeler[Solid],
    factors: tuple[float, float, float],
    maximum: tuple[float, float, float],
) -> None:
    scaled = cube_mm(modeler, 1.0, 1.0, 1.0).scale(factors)
    assert_box_close(scaled.bounding_box, (0.0, 0.0, 0.0), maximum, tolerance=1e-5)


def test_mirror(modeler: Modeler[Solid]) -> None:
    mirrored = cube_mm(modeler, 1.0, 2.0, 3.0).mirror((2.0, 0.0, 0.0))
    assert_box_close(mirrored.bounding_box, (-1.0, 0.0, 0.0), (0.0, 2.0, 3.0))


@pytest.mark.parametrize("factors", [(0.0, 1.0, 1.0), (1.0, -2.0, 1.0), (1.0, 1.0, math.inf)])
def test_scale_rejects_invalid_factors(
    modeler: Modeler[Solid], factors: tuple[float, float, float]
) -> None:
    with pytest.raises(ValueError, match="factors"):
        cube_mm(modeler, 1.0, 1.0, 1.0).scale(factors)


def test_mirror_rejects_zero_normal(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="zero vector"):
        cube_mm(modeler, 1.0, 1.0, 1.0).mirror((0.0, 0.0, 0.0))


def test_rotate_rejects_non_finite_angle(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="angle"):
        cube_mm(modeler, 1.0, 1.0, 1.0).rotate(Axis.Y, math.inf * DEGREE)


def test_combining_backends_raises_type_error() -> None:
    scad_box: Solid = cube_mm(CADBackend.PYTHONSCAD.create_modeler(AUTOCAD), 1.0, 1.0, 1.0)
    cadquery_box: Solid = cube_mm(CADBackend.CADQUERY.create_modeler(AUTOCAD), 1.0, 1.0, 1.0)
    for combine in (Solid.union, Solid.difference, Solid.intersection):
        with pytest.raises(TypeError, match="same backend"):
            combine(scad_box, cadquery_box)
