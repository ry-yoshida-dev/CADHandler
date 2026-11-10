from pathlib import Path

import pytest

from cad_handler import ExportFormat, Modeler, Solid, UnsupportedExportFormatError


def test_exports_every_supported_format(modeler: Modeler[Solid], tmp_path: Path) -> None:
    solid = modeler.box((2.0, 2.0, 2.0)) - modeler.sphere(radius=1.2)
    for export_format in solid.supported_export_formats:
        path = tmp_path / f"part{export_format.value}"
        solid.export(path)
        assert path.stat().st_size > 0, export_format


def test_both_backends_share_stl_three_mf_and_step(modeler: Modeler[Solid]) -> None:
    box = modeler.box((1.0, 1.0, 1.0))
    common = {ExportFormat.STL, ExportFormat.THREE_MF, ExportFormat.STEP}
    assert common <= box.supported_export_formats


def test_unsupported_format_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    box = modeler.box((1.0, 1.0, 1.0))
    unsupported = set(ExportFormat) - box.supported_export_formats
    assert unsupported
    for export_format in unsupported:
        path = tmp_path / f"part{export_format.value}"
        with pytest.raises(UnsupportedExportFormatError) as error:
            box.export(path)
        assert error.value.export_format is export_format
        assert not path.exists()


def test_unknown_suffix_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown export suffix"):
        modeler.box((1.0, 1.0, 1.0)).export(tmp_path / "part.xyz")


def test_missing_parent_directory_raises(modeler: Modeler[Solid], tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        modeler.box((1.0, 1.0, 1.0)).export(tmp_path / "missing" / "part.stl")
