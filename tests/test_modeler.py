import math

import pytest

from cad_handler import Modeler, Solid
from cad_handler.pythonscad import PythonSCADModeler

from .conftest import CURVED_TOLERANCE, assert_box_close


def test_box_starts_at_origin(modeler: Modeler[Solid]) -> None:
    box = modeler.box((1.0, 2.0, 3.0))
    assert_box_close(box.bounding_box, (0.0, 0.0, 0.0), (1.0, 2.0, 3.0))


def test_centered_box(modeler: Modeler[Solid]) -> None:
    box = modeler.box((2.0, 4.0, 6.0), is_centered=True)
    assert_box_close(box.bounding_box, (-1.0, -2.0, -3.0), (1.0, 2.0, 3.0))


def test_cylinder_stands_on_xy_plane(modeler: Modeler[Solid]) -> None:
    cylinder = modeler.cylinder(radius=2.0, height=5.0)
    assert_box_close(cylinder.bounding_box, (-2.0, -2.0, 0.0), (2.0, 2.0, 5.0), CURVED_TOLERANCE)


def test_centered_cylinder(modeler: Modeler[Solid]) -> None:
    cylinder = modeler.cylinder(radius=1.0, height=4.0, is_centered=True)
    assert_box_close(cylinder.bounding_box, (-1.0, -1.0, -2.0), (1.0, 1.0, 2.0), CURVED_TOLERANCE)


def test_sphere_is_centered(modeler: Modeler[Solid]) -> None:
    sphere = modeler.sphere(radius=3.0)
    tolerance = 3.0 * CURVED_TOLERANCE
    assert_box_close(sphere.bounding_box, (-3.0, -3.0, -3.0), (3.0, 3.0, 3.0), tolerance)


@pytest.mark.parametrize("size", [(0.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, math.inf)])
def test_box_rejects_invalid_size(
    modeler: Modeler[Solid], size: tuple[float, float, float]
) -> None:
    with pytest.raises(ValueError, match="size"):
        modeler.box(size)


def test_cylinder_rejects_invalid_dimensions(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="radius"):
        modeler.cylinder(radius=0.0, height=1.0)
    with pytest.raises(ValueError, match="height"):
        modeler.cylinder(radius=1.0, height=math.nan)


def test_sphere_rejects_invalid_radius(modeler: Modeler[Solid]) -> None:
    with pytest.raises(ValueError, match="radius"):
        modeler.sphere(radius=-1.0)


def test_pythonscad_rejects_too_few_segments() -> None:
    with pytest.raises(ValueError, match="segment_count"):
        PythonSCADModeler(segment_count=2)


def test_pythonscad_segment_count_controls_smoothness() -> None:
    coarse = PythonSCADModeler(segment_count=4).cylinder(radius=1.0, height=1.0)
    fine = PythonSCADModeler(segment_count=128).cylinder(radius=1.0, height=1.0)
    coarse_points, _ = coarse.native.mesh()
    fine_points, _ = fine.native.mesh()
    assert len(coarse_points) == 2 * 4
    assert len(fine_points) == 2 * 128
