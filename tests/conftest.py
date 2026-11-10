import pytest

from cad_handler import BoundingBox, CADBackend, Modeler, Solid, Vector3

# Mesh backends approximate curves with segments, so curved extents are compared loosely.
CURVED_TOLERANCE = 0.02


@pytest.fixture(params=list(CADBackend), ids=lambda backend: backend.value)
def modeler(request: pytest.FixtureRequest) -> Modeler[Solid]:
    backend: CADBackend = request.param
    return backend.create_modeler()


def assert_box_close(
    actual: BoundingBox, minimum: Vector3, maximum: Vector3, tolerance: float = 1e-6
) -> None:
    assert actual.minimum == pytest.approx(minimum, abs=tolerance)
    assert actual.maximum == pytest.approx(maximum, abs=tolerance)
