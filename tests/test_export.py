import re
from pathlib import Path

import numpy as np
import pytest
from units import Length, LengthUnit

from cad_handler import (
    CoordinateUnitRequiredError,
    ExportFormat,
    Modeler,
    Solid,
    UnsupportedExportFormatError,
)

from .conftest import MM, cube_mm

INCH = Length(value=np.array([1.0]), unit=LengthUnit.INCH)


def read_stl_vertices(path: Path) -> np.ndarray[tuple[int, int], np.dtype[np.float64]]:
    data = path.read_bytes()
    triangle_count = int(np.frombuffer(data, dtype="<u4", count=1, offset=80)[0])
    if len(data) == 84 + 50 * triangle_count:
        record = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("flags", "<u2")])
        triangles = np.frombuffer(data, dtype=record, count=triangle_count, offset=84)
        return triangles["vertices"].reshape(-1, 3).astype(np.float64)
    numbers = re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data)
    return np.array(numbers, dtype=np.float64)


def export_unit(solid: Solid, export_format: ExportFormat) -> Length | None:
    return None if export_format in solid.unit_recording_formats else MM


def test_exports_every_supported_format(modeler: Modeler[Solid], tmp_path: Path) -> None:
    solid = cube_mm(modeler, 2.0, 2.0, 2.0) - modeler.sphere(1.2 * MM)
    for export_format in solid.supported_export_formats:
        path = tmp_path / f"part{export_format.value}"
        solid.export(path, export_unit(solid, export_format))
        assert path.stat().st_size > 0, export_format


def test_unit_recording_formats_are_supported(modeler: Modeler[Solid]) -> None:
    box = cube_mm(modeler, 1.0, 1.0, 1.0)
    assert box.unit_recording_formats <= box.supported_export_formats
    assert ExportFormat.THREE_MF in box.unit_recording_formats


def test_both_backends_share_stl_three_mf_and_step(modeler: Modeler[Solid]) -> None:
    box = cube_mm(modeler, 1.0, 1.0, 1.0)
    common = {ExportFormat.STL, ExportFormat.THREE_MF, ExportFormat.STEP}
    assert common <= box.supported_export_formats


def test_coordinate_unit_scales_unitless_numbers(modeler: Modeler[Solid], tmp_path: Path) -> None:
    box = cube_mm(modeler, 25.4, 50.8, 12.7)
    in_inches, in_millimeters = tmp_path / "inch.stl", tmp_path / "millimeter.stl"
    box.export(in_inches, INCH)
    box.export(in_millimeters, MM)
    np.testing.assert_allclose(read_stl_vertices(in_inches).max(axis=0), [1.0, 2.0, 0.5], atol=1e-5)
    np.testing.assert_allclose(
        read_stl_vertices(in_millimeters).max(axis=0), [25.4, 50.8, 12.7], atol=1e-4
    )


def test_unitless_format_requires_coordinate_unit(modeler: Modeler[Solid], tmp_path: Path) -> None:
    path = tmp_path / "part.stl"
    with pytest.raises(CoordinateUnitRequiredError) as error:
        cube_mm(modeler, 1.0, 1.0, 1.0).export(path)
    assert error.value.export_format is ExportFormat.STL
    assert not path.exists()


def test_unit_recording_format_rejects_coordinate_unit(
    modeler: Modeler[Solid], tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="records the unit"):
        cube_mm(modeler, 1.0, 1.0, 1.0).export(tmp_path / "part.3mf", MM)


def test_rejects_zero_coordinate_unit(modeler: Modeler[Solid], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="coordinate_unit"):
        cube_mm(modeler, 1.0, 1.0, 1.0).export(tmp_path / "part.stl", 0.0 * MM)


def test_unsupported_format_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    box = cube_mm(modeler, 1.0, 1.0, 1.0)
    unsupported = set(ExportFormat) - box.supported_export_formats
    assert unsupported
    for export_format in unsupported:
        path = tmp_path / f"part{export_format.value}"
        with pytest.raises(UnsupportedExportFormatError) as error:
            box.export(path, MM)
        assert error.value.export_format is export_format
        assert not path.exists()


def test_unknown_suffix_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown export suffix"):
        cube_mm(modeler, 1.0, 1.0, 1.0).export(tmp_path / "part.xyz", MM)


def test_missing_parent_directory_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        cube_mm(modeler, 1.0, 1.0, 1.0).export(tmp_path / "missing" / "part.stl", MM)
