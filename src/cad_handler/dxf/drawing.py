from pathlib import Path

import numpy as np
from cartesian_axis import SoftwareCoordinateSystem
from ezdxf import edgeminer, edgesmith, path
from ezdxf.document import Drawing
from ezdxf.entities.arc import Arc
from ezdxf.entities.circle import Circle
from ezdxf.entities.dxfgfx import DXFGraphic
from ezdxf.entities.ellipse import Ellipse
from ezdxf.entities.line import Line
from ezdxf.entities.lwpolyline import LWPolyline
from ezdxf.entities.polyline import Polyline
from ezdxf.entities.spline import Spline
from ezdxf.filemanagement import readfile  # pyright: ignore[reportUnknownVariableType]  # bare PathLike upstream
from ezdxf.upright import upright_all
from units import Length, LengthUnit

from ..errors import NonPlanarEntityError, OpenProfileError
from ..profile import Loop, Profile
from ..scalar import single_finite_value
from .insertion_unit import InsertionUnit

_CURVE_TYPES: tuple[type[DXFGraphic], ...] = (
    Line,
    Arc,
    Circle,
    Ellipse,
    Spline,
    LWPolyline,
    Polyline,
)


class DXFDrawing:
    """
    DXF drawing read for the planar profiles drawn on its layers.

    Parameters
    ----------
    document : Drawing
        The ezdxf document.
    drawing_unit : Length
        Length one drawing unit stands for, as a single value.

    Raises
    ------
    ValueError
        If ``drawing_unit`` is not a single finite, positive value.
    """

    def __init__(self, document: Drawing, drawing_unit: Length) -> None:
        if single_finite_value("drawing_unit", drawing_unit.value) <= 0:
            raise ValueError(f"drawing_unit must be positive, got {drawing_unit}.")
        self._document: Drawing = document
        self._drawing_unit: Length = drawing_unit

    @classmethod
    def read(cls, path: Path, drawing_unit: Length | None = None) -> "DXFDrawing":
        """
        Read a DXF file.

        Parameters
        ----------
        path : Path
            The DXF file.
        drawing_unit : Length | None
            Length one drawing unit stands for. ``None`` takes it from the
            file's ``$INSUNITS`` header; a given value overrides the header.

        Returns
        -------
        DXFDrawing
            The drawing.

        Raises
        ------
        FileNotFoundError
            If ``path`` is not a file.
        UnknownDrawingUnitError
            If ``drawing_unit`` is ``None`` and the header states no known unit.
        ValueError
            If ``drawing_unit`` is not a single finite, positive value.
        """
        if not path.is_file():
            raise FileNotFoundError(f"No DXF file at {path}.")
        document = readfile(str(path))
        if drawing_unit is None:
            code = int(document.header.get("$INSUNITS", InsertionUnit.UNITLESS.value))
            drawing_unit = InsertionUnit.from_code(code).length
        return cls(document, drawing_unit)

    @property
    def drawing_unit(self) -> Length:
        """Length one drawing unit stands for."""
        return self._drawing_unit

    @property
    def layers(self) -> frozenset[str]:
        """Names of the layers that hold model-space entities."""
        return frozenset(entity.dxf.layer for entity in self._document.modelspace())

    def profile(self, layer: str, tolerance: Length) -> Profile:
        """
        Read the closed loops drawn on a layer as a profile.

        Lines, arcs, circles, ellipses, splines, and polylines are read; other
        entities such as text and dimensions are ignored. Open curves are
        joined end to end into loops, and curved segments are approximated by
        straight ones.

        Parameters
        ----------
        layer : str
            Layer name, compared case-insensitively as AutoCAD does.
        tolerance : Length
            Largest gap between curve ends that still joins them, and largest
            distance between a curve and its straight-segment approximation.

        Returns
        -------
        Profile
            The loops in drawing units, with ``drawing_unit`` as their unit, in
            ``SoftwareCoordinateSystem.AUTOCAD``.

        Raises
        ------
        ValueError
            If ``tolerance`` is not a single finite, positive value, or the
            layer holds no curve.
        NonPlanarEntityError
            If a curve leaves the xy plane.
        OpenProfileError
            If some curves do not close into loops.
        """
        tolerance_in_meters = single_finite_value("tolerance", tolerance.in_unit(LengthUnit.M))
        if tolerance_in_meters <= 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}.")
        unit_in_meters = float(self._drawing_unit.in_unit(LengthUnit.M).item())
        drawing_tolerance = tolerance_in_meters / unit_in_meters

        curves = self._planar_curves(layer)
        closed_curves = [curve for curve in curves if edgesmith.is_closed_entity(curve)]
        open_curves = [curve for curve in curves if not edgesmith.is_closed_entity(curve)]

        loops = [_flatten(path.make_path(curve), drawing_tolerance) for curve in closed_curves]
        edges = list(edgesmith.edges_from_entities_2d(open_curves, gap_tol=drawing_tolerance))
        if edges:
            loops.extend(_join_into_loops(layer, edges, drawing_tolerance))
        if not loops:
            raise ValueError(f"Layer {layer!r} holds no curve.")
        return Profile(
            loops=tuple(loops),
            coordinate_unit=self._drawing_unit,
            coordinate_system=SoftwareCoordinateSystem.AUTOCAD.coordinate_system,
        )

    def _planar_curves(self, layer: str) -> list[DXFGraphic]:
        layer_key = layer.casefold()
        # Copies keep upright_all from changing the document.
        curves = [
            entity.copy()
            for entity in self._document.modelspace()
            if isinstance(entity, _CURVE_TYPES) and entity.dxf.layer.casefold() == layer_key
        ]
        # Mirrored entities carry a (0, 0, -1) extrusion; flipping it keeps their shape.
        upright_all(curves)
        for curve in curves:
            if not edgesmith.is_pure_2d_entity(curve):
                raise NonPlanarEntityError(layer, curve.dxftype())
        return curves


def _join_into_loops(layer: str, edges: list[edgeminer.Edge], tolerance: float) -> list[Loop]:
    chains = edgeminer.find_all_simple_chains(edgeminer.Deposit(edges, gap_tol=tolerance))
    open_chain_count = sum(not edgeminer.is_loop(chain, gap_tol=tolerance) for chain in chains)
    if open_chain_count:
        raise OpenProfileError(layer, open_chain_count)
    return [_flatten(edgesmith.path2d_from_chain(chain), tolerance) for chain in chains]


def _flatten(curve_path: path.Path, tolerance: float) -> Loop:
    vertices = np.array(
        [(vertex.x, vertex.y) for vertex in curve_path.flattening(distance=tolerance)],
        dtype=np.float64,
    )
    if len(vertices) > 1 and np.allclose(vertices[0], vertices[-1], rtol=0.0, atol=tolerance):
        return vertices[:-1]
    return vertices
