from pathlib import Path
from typing import ClassVar, Literal, Self, override

from cadquery import Matrix, Shape, exporters

from ..bounding_box import BoundingBox
from ..errors import EmptySolidError, UnsupportedExportFormatError
from ..export_format import ExportFormat
from ..solid import Solid
from ..vector import Vector3

_ORIGIN: Vector3 = (0.0, 0.0, 0.0)
_AXES: tuple[Vector3, Vector3, Vector3] = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

type _CadQueryExportType = Literal["STL", "STEP", "3MF", "BREP"]


class CadQuerySolid(Solid):
    """
    Solid backed by a CadQuery (OpenCASCADE) boundary representation.

    Parameters
    ----------
    native : Shape
        The wrapped CadQuery shape, for features this package does not cover.
    """

    backend_name: ClassVar[str] = "CadQuery"
    supported_export_formats: ClassVar[frozenset[ExportFormat]] = frozenset(
        {ExportFormat.STL, ExportFormat.THREE_MF, ExportFormat.STEP, ExportFormat.BREP}
    )

    def __init__(self, native: Shape) -> None:
        self._native: Shape = native

    @property
    def native(self) -> Shape:
        """The wrapped CadQuery shape."""
        return self._native

    @property
    @override
    def bounding_box(self) -> BoundingBox:
        if not self._native.Solids():
            raise EmptySolidError("The CadQuery solid has no volume.")
        box = self._native.BoundingBox()
        return BoundingBox(
            minimum=(box.xmin, box.ymin, box.zmin), maximum=(box.xmax, box.ymax, box.zmax)
        )

    @override
    def _union(self, other: Solid) -> Self:
        return type(self)(self._native.fuse(self._as_same_backend(other)._native))

    @override
    def _difference(self, other: Solid) -> Self:
        return type(self)(self._native.cut(self._as_same_backend(other)._native))

    @override
    def _intersection(self, other: Solid) -> Self:
        return type(self)(self._native.intersect(self._as_same_backend(other)._native))

    @override
    def _translate(self, offset: Vector3) -> Self:
        return type(self)(self._native.translate(offset))

    @override
    def _rotate(self, angles: Vector3) -> Self:
        rotated = self._native
        for axis, angle in zip(_AXES, angles, strict=True):
            if angle != 0:
                rotated = rotated.rotate(_ORIGIN, axis, angle)
        return type(self)(rotated)

    @override
    def _scale(self, factors: Vector3) -> Self:
        x_factor, y_factor, z_factor = factors
        if x_factor == y_factor == z_factor:
            # Uniform scaling keeps lines and circles exact; transformGeometry may turn them into splines.
            return type(self)(self._native.scale(x_factor))
        matrix = Matrix(
            [
                [x_factor, 0.0, 0.0, 0.0],
                [0.0, y_factor, 0.0, 0.0],
                [0.0, 0.0, z_factor, 0.0],
            ]
        )
        return type(self)(self._native.transformGeometry(matrix))

    @override
    def _mirror(self, normal: Vector3) -> Self:
        return type(self)(self._native.mirror(normal, _ORIGIN))

    @override
    def _export(self, path: Path, export_format: ExportFormat) -> None:
        exporters.export(self._native, str(path), exportType=_to_export_type(export_format))


def _to_export_type(export_format: ExportFormat) -> _CadQueryExportType:
    match export_format:
        case ExportFormat.STL:
            return "STL"
        case ExportFormat.STEP:
            return "STEP"
        case ExportFormat.THREE_MF:
            return "3MF"
        case ExportFormat.BREP:
            return "BREP"
        case ExportFormat.OBJ | ExportFormat.OFF:
            raise UnsupportedExportFormatError(
                export_format, CadQuerySolid.backend_name, CadQuerySolid.supported_export_formats
            )
