import numpy as np
import pytest
from cartesian_axis import SoftwareCoordinateSystem
from units import Angle, AngleUnit, Length, LengthUnit, MetricPrefix

from cad_handler import BoundingBox, CADBackend, Displacement, Modeler, Solid, Vector3

# Mesh backends approximate curves with segments, so curved extents are compared loosely.
CURVED_TOLERANCE = 0.02

# AutoCAD's world coordinate system: x right, y forward, z up, right-handed.
AUTOCAD = SoftwareCoordinateSystem.AUTOCAD.coordinate_system

MM = Length(value=np.array([1.0]), unit=LengthUnit.M, prefix=MetricPrefix.MILLI)
DEGREE = Angle(value=np.array([1.0]), unit=AngleUnit.DEGREE)


@pytest.fixture(params=list(CADBackend), ids=lambda backend: backend.value)
def modeler(request: pytest.FixtureRequest) -> Modeler[Solid]:
    backend: CADBackend = request.param
    return backend.create_modeler(AUTOCAD)


def offset_mm(x: float, y: float, z: float) -> Displacement:
    return Displacement.from_signed_values((x, y, z), LengthUnit.M, MetricPrefix.MILLI)


def cube_mm(modeler: Modeler[Solid], x: float, y: float, z: float) -> Solid:
    return modeler.box(x * MM, y * MM, z * MM)


def assert_box_close(
    actual: BoundingBox, minimum: Vector3, maximum: Vector3, tolerance: float = 1e-6
) -> None:
    """Compare corners given in millimeters."""
    milli = (LengthUnit.M, MetricPrefix.MILLI)
    assert actual.minimum.signed_values(*milli) == pytest.approx(minimum, abs=tolerance)
    assert actual.maximum.signed_values(*milli) == pytest.approx(maximum, abs=tolerance)
