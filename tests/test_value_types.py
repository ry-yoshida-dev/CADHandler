from pathlib import Path

import pytest

from cad_handler import BoundingBox, CADBackend, ExportFormat, Modeler, Solid
from cad_handler.cadquery import CadQueryModeler
from cad_handler.pythonscad import PythonSCADModeler


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("part.stl", ExportFormat.STL),
        ("part.STL", ExportFormat.STL),
        ("part.3mf", ExportFormat.THREE_MF),
        ("part.step", ExportFormat.STEP),
        ("part.stp", ExportFormat.STEP),
        ("part.obj", ExportFormat.OBJ),
        ("part.off", ExportFormat.OFF),
        ("part.brep", ExportFormat.BREP),
    ],
)
def test_export_format_from_path(file_name: str, expected: ExportFormat) -> None:
    assert ExportFormat.from_path(Path(file_name)) is expected


@pytest.mark.parametrize("file_name", ["part", "part.txt"])
def test_export_format_rejects_unknown_suffix(file_name: str) -> None:
    with pytest.raises(ValueError, match="Unknown export suffix"):
        ExportFormat.from_path(Path(file_name))


def test_bounding_box_size_and_center() -> None:
    box = BoundingBox(minimum=(-1.0, 0.0, 2.0), maximum=(3.0, 2.0, 2.0))
    assert box.size == (4.0, 2.0, 0.0)
    assert box.center == (1.0, 1.0, 2.0)


def test_bounding_box_rejects_inverted_corners() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        BoundingBox(minimum=(0.0, 1.0, 0.0), maximum=(1.0, 0.0, 1.0))


@pytest.mark.parametrize(
    ("backend", "modeler_type"),
    [(CADBackend.PYTHONSCAD, PythonSCADModeler), (CADBackend.CADQUERY, CadQueryModeler)],
)
def test_backend_creates_its_modeler(
    backend: CADBackend, modeler_type: type[Modeler[Solid]]
) -> None:
    assert isinstance(backend.create_modeler(), modeler_type)
