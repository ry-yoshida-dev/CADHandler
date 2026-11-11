import math

import numpy as np
import pytest
from cartesian_axis import Axis, SoftwareCoordinateSystem
from units import Length, LengthUnit, MetricPrefix

from cad_handler import CoordinateSystemMismatchError, EmptySolidError, Modeler, Profile, Solid
from cad_handler.pythonscad import PythonSCADModeler

from .conftest import AUTOCAD, CURVED_TOLERANCE, MM, assert_box_close, cube_mm, offset_mm


def test_box_starts_at_origin(modeler: Modeler[Solid]) -> None:
    box = cube_mm(modeler, 1.0, 2.0, 3.0)
    assert_box_close(box.bounding_box, (0.0, 0.0, 0.0), (1.0, 2.0, 3.0))


def test_centered_box(modeler: Modeler[Solid]) -> None:
    box = modeler.box(2.0 * MM, 4.0 * MM, 6.0 * MM, is_centered=True)
    assert_box_close(box.bounding_box, (-1.0, -2.0, -3.0), (1.0, 2.0, 3.0))


def test_box_converts_units(modeler: Modeler[Solid]) -> None:
    box = modeler.box(
        Length(value=np.array([1.0]), unit=LengthUnit.INCH),
        Length(value=np.array([2.0]), unit=LengthUnit.M, prefix=MetricPrefix.CENTI),
        3.0 * MM,
    )
    assert_box_close(box.bounding_box, (0.0, 0.0, 0.0), (25.4, 20.0, 3.0))


@pytest.mark.parametrize(
    ("axis", "minimum", "maximum"),
    [
        (Axis.X, (0.0, -2.0, -2.0), (5.0, 2.0, 2.0)),
        (Axis.Y, (-2.0, 0.0, -2.0), (2.0, 5.0, 2.0)),
        (Axis.Z, (-2.0, -2.0, 0.0), (2.0, 2.0, 5.0)),
    ],
    ids=["x", "y", "z"],
)
def test_cylinder_runs_along_axis_from_origin(
    modeler: Modeler[Solid],
    axis: Axis,
    minimum: tuple[float, float, float],
    maximum: tuple[float, float, float],
) -> None:
    cylinder = modeler.cylinder(radius=2.0 * MM, height=5.0 * MM, axis=axis)
    assert_box_close(cylinder.bounding_box, minimum, maximum, CURVED_TOLERANCE)


def test_centered_cylinder(modeler: Modeler[Solid]) -> None:
    cylinder = modeler.cylinder(radius=1.0 * MM, height=4.0 * MM, axis=Axis.Z, is_centered=True)
    assert_box_close(cylinder.bounding_box, (-1.0, -1.0, -2.0), (1.0, 1.0, 2.0), CURVED_TOLERANCE)


def test_sphere_is_centered(modeler: Modeler[Solid]) -> None:
    sphere = modeler.sphere(3.0 * MM)
    tolerance = 3.0 * CURVED_TOLERANCE
    assert_box_close(sphere.bounding_box, (-3.0, -3.0, -3.0), (3.0, 3.0, 3.0), tolerance)


@pytest.mark.parametrize("size", [(0.0, 1.0, 1.0), (1.0, math.inf, 1.0)], ids=["zero", "infinite"])
def test_box_rejects_invalid_size(
    modeler: Modeler[Solid], size: tuple[float, float, float]
) -> None:
    with pytest.raises(ValueError, match=r"^(x|y) must be"):
        cube_mm(modeler, *size)


def test_box_rejects_multiple_values(modeler: Modeler[Solid]) -> None:
    two_values = Length(value=np.array([1.0, 2.0]), unit=LengthUnit.M)
    with pytest.raises(ValueError, match="single value"):
        modeler.box(two_values, 1.0 * MM, 1.0 * MM)


def test_cylinder_rejects_invalid_dimensions(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="radius"):
        modeler.cylinder(radius=0.0 * MM, height=1.0 * MM, axis=Axis.Z)
    with pytest.raises(ValueError, match="height"):
        modeler.cylinder(radius=1.0 * MM, height=math.nan * MM, axis=Axis.Z)


def test_sphere_rejects_invalid_radius(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="radius"):
        modeler.sphere(0.0 * MM)


def test_pythonscad_rejects_too_few_segments() -> None:
    with pytest.raises(ValueError, match="segment_count"):
        PythonSCADModeler(AUTOCAD, segment_count=2)


def test_pythonscad_segment_count_controls_smoothness() -> None:
    coarse = PythonSCADModeler(AUTOCAD, segment_count=4).cylinder(1.0 * MM, 1.0 * MM, axis=Axis.Z)
    fine = PythonSCADModeler(AUTOCAD, segment_count=128).cylinder(1.0 * MM, 1.0 * MM, axis=Axis.Z)
    coarse_points, _ = coarse.native.mesh()
    fine_points, _ = fine.native.mesh()
    assert len(coarse_points) == 2 * 4
    assert len(fine_points) == 2 * 128


def test_extrude_cuts_holes_and_keeps_islands(modeler: Modeler[Solid]) -> None:
    outer = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    hole = np.array([[2.0, 2.0], [8.0, 2.0], [8.0, 8.0], [2.0, 8.0]])
    island = np.array([[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0]])
    plate = modeler.extrude(
        Profile(loops=(outer, hole, island), coordinate_unit=MM, coordinate_system=AUTOCAD),
        3.0 * MM,
    )
    assert_box_close(plate.bounding_box, (0.0, 0.0, 0.0), (10.0, 10.0, 3.0))

    def probe(x: float, y: float) -> Solid:
        return cube_mm(modeler, 0.5, 0.5, 1.0).translate(offset_mm(x, y, 1.0))

    with pytest.raises(EmptySolidError):
        _ = (plate & probe(2.5, 2.5)).bounding_box
    assert_box_close((plate & probe(4.5, 4.5)).bounding_box, (4.5, 4.5, 1.0), (5.0, 5.0, 2.0))


def test_extrude_rejects_invalid_height(modeler: Modeler[Solid]) -> None:
    triangle = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(ValueError, match="height"):
        modeler.extrude(
            Profile(loops=(triangle,), coordinate_unit=MM, coordinate_system=AUTOCAD), 0.0 * MM
        )


def test_combining_coordinate_systems_raises(modeler: Modeler[Solid]) -> None:
    unity = SoftwareCoordinateSystem.UNITY.coordinate_system
    in_unity = type(modeler)(unity).box(MM, MM, MM)
    with pytest.raises(CoordinateSystemMismatchError):
        _ = cube_mm(modeler, 1.0, 1.0, 1.0) | in_unity
