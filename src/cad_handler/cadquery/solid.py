from pathlib import Path
from typing import ClassVar, Literal, Self, override

from cadquery import Matrix, Shape, exporters
from cartesian_axis import Axis, CartesianCoordinateSystem

from ..errors import EmptySolidError, UnsupportedExportFormatError
from ..export_format import ExportFormat
from ..solid import Solid
from ..vector import Vector3

_ORIGIN: Vector3 = (0.0, 0.0, 0.0)

type _CadQueryExportType = Literal["STL", "STEP", "3MF", "BREP"]


class CadQuerySolid(Solid):
    """
    Solid backed by a CadQuery (OpenCASCADE) boundary representation.

    Parameters
    ----------
    native : Shape
        The wrapped CadQuery shape, for features this package does not cover.
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the geometry is expressed in.
    """

    backend_name: ClassVar[str] = "CadQuery"
    supported_export_formats: ClassVar[frozenset[ExportFormat]] = frozenset(
        {ExportFormat.STL, ExportFormat.THREE_MF, ExportFormat.STEP, ExportFormat.BREP}
    )
    unit_recording_formats: ClassVar[frozenset[ExportFormat]] = frozenset(
        {ExportFormat.THREE_MF, ExportFormat.STEP}
    )

    def __init__(self, native: Shape, coordinate_system: CartesianCoordinateSystem) -> None:
        super().__init__(coordinate_system)
        self._native: Shape = native

    @property
    def native(self) -> Shape:
        """The wrapped CadQuery shape."""
        return self._native

    def _wrap(self, native: Shape) -> Self:
        return type(self)(native, self.coordinate_system)

    @override
    def _with_coordinate_system(self, coordinate_system: CartesianCoordinateSystem) -> Self:
        return type(self)(self._native, coordinate_system)

    @override
    def _bounds(self) -> tuple[Vector3, Vector3]:
        if not self._native.Solids():
            raise EmptySolidError("The CadQuery solid has no volume.")
        box = self._native.BoundingBox()
        return (box.xmin, box.ymin, box.zmin), (box.xmax, box.ymax, box.zmax)

    @override
    def _union(self, other: Solid) -> Self:
        return self._wrap(self._native.fuse(self._as_same_backend(other)._native))

    @override
    def _difference(self, other: Solid) -> Self:
        return self._wrap(self._native.cut(self._as_same_backend(other)._native))

    @override
    def _intersection(self, other: Solid) -> Self:
        return self._wrap(self._native.intersect(self._as_same_backend(other)._native))

    @override
    def _translate(self, offset: Vector3) -> Self:
        return self._wrap(self._native.translate(offset))

    @override
    def _rotate(self, axis: Axis, degrees: float) -> Self:
        x, y, z = (float(component) for component in axis.unit_vector)
        return self._wrap(self._native.rotate(_ORIGIN, (x, y, z), degrees))

    @override
    def _scale(self, factors: Vector3) -> Self:
        x_factor, y_factor, z_factor = factors
        if x_factor == y_factor == z_factor:
            # Uniform scaling keeps lines and circles exact; transformGeometry may turn them into splines.
            return self._wrap(self._native.scale(x_factor))
        matrix = Matrix(
            [
                [x_factor, 0.0, 0.0, 0.0],
                [0.0, y_factor, 0.0, 0.0],
                [0.0, 0.0, z_factor, 0.0],
            ]
        )
        return self._wrap(self._native.transformGeometry(matrix))

    @override
    def _mirror(self, normal: Vector3) -> Self:
        return self._wrap(self._native.mirror(normal, _ORIGIN))

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
