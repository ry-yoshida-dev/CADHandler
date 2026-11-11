import numpy as np
import pytest
from cartesian_axis import CartesianCoordinateSystem, SoftwareCoordinateSystem

from cad_handler import AxisConversion, CADBackend, Modeler, Profile, Solid

from .conftest import AUTOCAD, MM, assert_box_close, cube_mm, offset_mm

UNITY = SoftwareCoordinateSystem.UNITY.coordinate_system
SYSTEMS: list[SoftwareCoordinateSystem] = list(SoftwareCoordinateSystem)


def corner_box(modeler: Modeler[Solid]) -> Solid:
    # Asymmetric about every axis, so any wrong swap or mirror shows in the bounds.
    return cube_mm(modeler, 1.0, 2.0, 3.0).translate(offset_mm(4.0, 5.0, 6.0))


@pytest.mark.parametrize("target", SYSTEMS, ids=lambda system: system.value)
def test_conversion_matches_converting_indices(
    modeler: Modeler[Solid], target: SoftwareCoordinateSystem
) -> None:
    converted = corner_box(modeler).to_coordinate_system(target.coordinate_system)
    indices = list(AUTOCAD.get_converting_indices(software_coordinate_system=target))
    low_x, low_y, low_z = np.array([4.0, 5.0, 6.0])[indices]
    high_x, high_y, high_z = np.array([5.0, 7.0, 9.0])[indices]
    assert converted.coordinate_system == target.coordinate_system
    assert_box_close(
        converted.bounding_box,
        (float(low_x), float(low_y), float(low_z)),
        (float(high_x), float(high_y), float(high_z)),
    )


def test_round_trip_restores_geometry(modeler: Modeler[Solid]) -> None:
    restored = corner_box(modeler).to_coordinate_system(UNITY).to_coordinate_system(AUTOCAD)
    assert restored.coordinate_system == AUTOCAD
    assert_box_close(restored.bounding_box, (4.0, 5.0, 6.0), (5.0, 7.0, 9.0))


def test_extrusion_is_converted_to_modeler_system() -> None:
    # The profile's z, AutoCAD's up axis, becomes Unity's up axis, y.
    rectangle = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [0.0, 1.0]])
    plan = Profile(loops=(rectangle,), coordinate_unit=MM, coordinate_system=AUTOCAD)
    for backend in CADBackend:
        solid = backend.create_modeler(UNITY).extrude(plan, 5.0 * MM)
        assert solid.coordinate_system == UNITY
        assert_box_close(solid.bounding_box, (0.0, 0.0, 0.0), (2.0, 5.0, 1.0))


def test_odd_permutations_mirror() -> None:
    systems: list[CartesianCoordinateSystem] = [system.coordinate_system for system in SYSTEMS]
    for source in systems:
        for target in systems:
            indices = source.get_converting_indices(
                software_coordinate_system=next(
                    system for system in SYSTEMS if system.coordinate_system == target
                )
            )
            is_odd = bool(np.linalg.det(np.eye(3)[list(indices)]) < 0)
            assert AxisConversion.between(source, target).is_mirrored is is_odd


def test_same_system_needs_no_operation() -> None:
    conversion = AxisConversion.between(AUTOCAD, AUTOCAD)
    assert not conversion.is_mirrored
    assert conversion.quarter_turns == (0, 0, 0)
