import math

import pytest

from cad_handler import CADBackend, EmptySolidError, Modeler, Solid

from .conftest import assert_box_close


def test_union_covers_both(modeler: Modeler[Solid]) -> None:
    first = modeler.box((1.0, 1.0, 1.0))
    second = modeler.box((1.0, 1.0, 1.0)).translate((2.0, 0.0, 0.0))
    assert_box_close(first.union(second).bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 1.0))
    assert_box_close((first | second).bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 1.0))


def test_difference_cuts_away(modeler: Modeler[Solid]) -> None:
    base = modeler.box((4.0, 1.0, 1.0))
    cutter = modeler.box((2.0, 3.0, 3.0)).translate((2.0, -1.0, -1.0))
    assert_box_close(base.difference(cutter).bounding_box, (0.0, 0.0, 0.0), (2.0, 1.0, 1.0))
    assert_box_close((base - cutter).bounding_box, (0.0, 0.0, 0.0), (2.0, 1.0, 1.0))


def test_intersection_keeps_overlap(modeler: Modeler[Solid]) -> None:
    first = modeler.box((2.0, 2.0, 2.0))
    second = modeler.box((2.0, 2.0, 2.0)).translate((1.0, 1.0, 1.0))
    assert_box_close(first.intersection(second).bounding_box, (1.0, 1.0, 1.0), (2.0, 2.0, 2.0))
    assert_box_close((first & second).bounding_box, (1.0, 1.0, 1.0), (2.0, 2.0, 2.0))


def test_full_difference_is_empty(modeler: Modeler[Solid]) -> None:
    box = modeler.box((1.0, 1.0, 1.0))
    with pytest.raises(EmptySolidError):
        _ = (box - box).bounding_box


def test_operations_leave_receiver_unchanged(modeler: Modeler[Solid]) -> None:
    box = modeler.box((1.0, 1.0, 1.0))
    box.translate((5.0, 5.0, 5.0)).rotate((0.0, 0.0, 45.0)).scale((2.0, 2.0, 2.0))
    _ = box | modeler.box((1.0, 1.0, 1.0)).translate((3.0, 0.0, 0.0))
    assert_box_close(box.bounding_box, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))


def test_translate(modeler: Modeler[Solid]) -> None:
    moved = modeler.box((1.0, 2.0, 3.0)).translate((1.0, -2.0, 3.0))
    assert_box_close(moved.bounding_box, (1.0, -2.0, 3.0), (2.0, 0.0, 6.0))


def test_rotate_applies_x_then_y_then_z(modeler: Modeler[Solid]) -> None:
    rotated = modeler.box((1.0, 2.0, 3.0)).rotate((90.0, 0.0, 90.0))
    assert_box_close(rotated.bounding_box, (0.0, 0.0, 0.0), (3.0, 1.0, 2.0))


def test_rotate_about_z_is_counterclockwise(modeler: Modeler[Solid]) -> None:
    rotated = modeler.box((1.0, 2.0, 3.0)).rotate((0.0, 0.0, 90.0))
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
    scaled = modeler.box((1.0, 1.0, 1.0)).scale(factors)
    assert_box_close(scaled.bounding_box, (0.0, 0.0, 0.0), maximum, tolerance=1e-5)


def test_mirror(modeler: Modeler[Solid]) -> None:
    mirrored = modeler.box((1.0, 2.0, 3.0)).mirror((2.0, 0.0, 0.0))
    assert_box_close(mirrored.bounding_box, (-1.0, 0.0, 0.0), (0.0, 2.0, 3.0))


@pytest.mark.parametrize("factors", [(0.0, 1.0, 1.0), (1.0, -2.0, 1.0), (1.0, 1.0, math.inf)])
def test_scale_rejects_invalid_factors(
    modeler: Modeler[Solid], factors: tuple[float, float, float]
) -> None:
    with pytest.raises(ValueError, match="factors"):
        modeler.box((1.0, 1.0, 1.0)).scale(factors)


def test_mirror_rejects_zero_normal(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="zero vector"):
        modeler.box((1.0, 1.0, 1.0)).mirror((0.0, 0.0, 0.0))


def test_transforms_reject_non_finite_values(modeler: Modeler[Solid]) -> None:
    box = modeler.box((1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="offset"):
        box.translate((math.nan, 0.0, 0.0))
    with pytest.raises(ValueError, match="angles"):
        box.rotate((0.0, math.inf, 0.0))


def test_combining_backends_raises_type_error() -> None:
    scad_box: Solid = CADBackend.PYTHONSCAD.create_modeler().box((1.0, 1.0, 1.0))
    cadquery_box: Solid = CADBackend.CADQUERY.create_modeler().box((1.0, 1.0, 1.0))
    for combine in (Solid.union, Solid.difference, Solid.intersection):
        with pytest.raises(TypeError, match="same backend"):
            combine(scad_box, cadquery_box)
