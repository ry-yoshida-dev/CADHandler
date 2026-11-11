# ezdxf annotates entity factories with partially unknown types (bare NumPy arrays and dicts).
# pyright: reportUnknownMemberType=false
from pathlib import Path

import numpy as np
import pytest
from ezdxf.document import Drawing
from ezdxf.filemanagement import new
from units import Length, LengthUnit, MetricPrefix

from cad_handler import (
    Modeler,
    NonPlanarEntityError,
    OpenProfileError,
    Solid,
    UnknownDrawingUnitError,
)
from cad_handler.dxf import DXFDrawing, InsertionUnit

from .conftest import CURVED_TOLERANCE, MM, assert_box_close

TOLERANCE = 0.001 * MM


def new_document(insertion_unit: InsertionUnit) -> Drawing:
    document = new()
    document.header["$INSUNITS"] = insertion_unit.value
    return document


def save(document: Drawing, directory: Path) -> Path:
    path = directory / "drawing.dxf"
    document.saveas(path)
    return path


def rectangle(document: Drawing, width: float, height: float, layer: str = "OUTLINE") -> None:
    points = [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]
    document.modelspace().add_lwpolyline(points, close=True, dxfattribs={"layer": layer})


def test_header_unit_scales_profile(modeler: Modeler[Solid], tmp_path: Path) -> None:
    document = new_document(InsertionUnit.INCH)
    rectangle(document, 10.0, 5.0)
    drawing = DXFDrawing.read(save(document, tmp_path))
    solid = modeler.extrude(drawing.profile("OUTLINE", TOLERANCE), 2.0 * MM)
    assert_box_close(solid.bounding_box, (0.0, 0.0, 0.0), (254.0, 127.0, 2.0))


def test_unitless_drawing_needs_unit(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.UNITLESS)
    rectangle(document, 1.0, 1.0)
    path = save(document, tmp_path)
    with pytest.raises(UnknownDrawingUnitError):
        DXFDrawing.read(path)
    meter = Length(value=np.array([1.0]), unit=LengthUnit.M)
    assert DXFDrawing.read(path, drawing_unit=meter).drawing_unit == meter


def test_given_unit_overrides_header(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.METER)
    rectangle(document, 3.0, 1.0)
    drawing = DXFDrawing.read(save(document, tmp_path), drawing_unit=1.0 * MM)
    (loop,) = drawing.profile("OUTLINE", TOLERANCE).loops_in(LengthUnit.M, MetricPrefix.MILLI)
    assert loop.max(axis=0) == pytest.approx([3.0, 1.0])


def test_lines_and_arcs_join_into_loop(modeler: Modeler[Solid], tmp_path: Path) -> None:
    # A 20 x 10 slot with a half-round right end, drawn as separate entities.
    document = new_document(InsertionUnit.MILLIMETER)
    space = document.modelspace()
    attributes = {"layer": "Slot"}
    space.add_line((0.0, 0.0), (20.0, 0.0), dxfattribs=attributes)
    space.add_arc((20.0, 5.0), 5.0, start_angle=-90.0, end_angle=90.0, dxfattribs=attributes)
    space.add_line((20.0, 10.0), (0.0, 10.0), dxfattribs=attributes)
    space.add_line((0.0, 10.0), (0.0, 0.0), dxfattribs=attributes)
    space.add_text("ignored", dxfattribs=attributes)
    drawing = DXFDrawing.read(save(document, tmp_path))
    assert drawing.layers == frozenset({"Slot"})
    solid = modeler.extrude(drawing.profile("SLOT", TOLERANCE), 1.0 * MM)
    assert_box_close(solid.bounding_box, (0.0, 0.0, 0.0), (25.0, 10.0, 1.0), CURVED_TOLERANCE)


def test_circle_inside_outline_is_hole(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    rectangle(document, 10.0, 10.0)
    document.modelspace().add_circle((5.0, 5.0), 2.0, dxfattribs={"layer": "OUTLINE"})
    profile = DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", TOLERANCE)
    assert sorted(profile.nesting_depths) == [0, 1]


def test_mirrored_arc_is_read_upright(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    space = document.modelspace()
    # With extrusion (0, 0, -1), this arc spans the left half of a circle around (0, 0).
    space.add_arc(
        (0.0, 0.0),
        1.0,
        start_angle=-90.0,
        end_angle=90.0,
        dxfattribs={"layer": "OUTLINE", "extrusion": (0.0, 0.0, -1.0)},
    )
    space.add_line((0.0, 1.0), (0.0, -1.0), dxfattribs={"layer": "OUTLINE"})
    profile = DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", TOLERANCE)
    (loop,) = profile.loops
    assert loop[:, 0].min() == pytest.approx(-1.0, abs=TOLERANCE.value.item())
    assert loop[:, 0].max() == pytest.approx(0.0)


def test_open_chain_raises(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    space = document.modelspace()
    space.add_line((0.0, 0.0), (1.0, 0.0), dxfattribs={"layer": "OUTLINE"})
    space.add_line((1.0, 0.0), (1.0, 1.0), dxfattribs={"layer": "OUTLINE"})
    with pytest.raises(OpenProfileError) as error:
        DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", TOLERANCE)
    assert error.value.open_chain_count == 1


def test_gap_within_tolerance_closes(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    space = document.modelspace()
    for start, end in [((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (0, 1.0005)), ((0, 1), (0, 0))]:
        space.add_line(start, end, dxfattribs={"layer": "OUTLINE"})
    drawing = DXFDrawing.read(save(document, tmp_path))
    assert len(drawing.profile("OUTLINE", 0.001 * MM).loops) == 1
    with pytest.raises(OpenProfileError):
        drawing.profile("OUTLINE", 0.0001 * MM)


def test_curve_off_the_plane_raises(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    document.modelspace().add_line((0, 0, 0), (1, 0, 1), dxfattribs={"layer": "OUTLINE"})
    with pytest.raises(NonPlanarEntityError, match="LINE"):
        DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", TOLERANCE)


def test_layer_without_curves_raises(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    rectangle(document, 1.0, 1.0)
    with pytest.raises(ValueError, match="holds no curve"):
        DXFDrawing.read(save(document, tmp_path)).profile("MISSING", TOLERANCE)


def test_rejects_invalid_tolerance(tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    rectangle(document, 1.0, 1.0)
    with pytest.raises(ValueError, match="tolerance"):
        DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", 0.0 * MM)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        DXFDrawing.read(tmp_path / "missing.dxf")


@pytest.mark.parametrize(
    ("insertion_unit", "meters"),
    [
        (InsertionUnit.MILLIMETER, 1e-3),
        (InsertionUnit.FOOT, 0.3048),
        (InsertionUnit.MIL, 2.54e-5),
        (InsertionUnit.ANGSTROM, 1e-10),
        (InsertionUnit.US_SURVEY_FOOT, 0.3048006096),
        (InsertionUnit.PARSEC, 3.0856775814913673e16),
    ],
)
def test_insertion_unit_lengths(insertion_unit: InsertionUnit, meters: float) -> None:
    assert insertion_unit.length.meter.item() == pytest.approx(meters)


def test_every_insertion_unit_but_unitless_has_length() -> None:
    for insertion_unit in InsertionUnit:
        if insertion_unit is not InsertionUnit.UNITLESS:
            assert insertion_unit.length.meter.item() > 0


def test_unknown_insertion_code_raises() -> None:
    with pytest.raises(UnknownDrawingUnitError, match="99"):
        InsertionUnit.from_code(99)


def test_extruded_profile_exports(modeler: Modeler[Solid], tmp_path: Path) -> None:
    document = new_document(InsertionUnit.MILLIMETER)
    rectangle(document, 4.0, 2.0)
    profile = DXFDrawing.read(save(document, tmp_path)).profile("OUTLINE", TOLERANCE)
    solid = modeler.extrude(profile, 1.0 * MM)
    path = tmp_path / "plate.3mf"
    solid.export(path)
    assert path.stat().st_size > 0
