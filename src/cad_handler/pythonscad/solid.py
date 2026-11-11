from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Self, override

import numpy as np
from cartesian_axis import Axis, CartesianCoordinateSystem

from ..errors import EmptySolidError
from ..export_format import ExportFormat
from ..solid import Solid
from ..vector import Vector3

if TYPE_CHECKING:
    # PythonSCAD names this type but does not export it at runtime.
    from openscad import PyOpenSCAD


class PythonSCADSolid(Solid):
    """
    Solid backed by a PythonSCAD (OpenSCAD) object, evaluated as a polygon mesh.

    Parameters
    ----------
    native : PyOpenSCAD
        The wrapped PythonSCAD object, for features this package does not cover.
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the geometry is expressed in.
    """

    backend_name: ClassVar[str] = "PythonSCAD"
    supported_export_formats: ClassVar[frozenset[ExportFormat]] = frozenset(
        {
            ExportFormat.STL,
            ExportFormat.THREE_MF,
            ExportFormat.STEP,
            ExportFormat.OBJ,
            ExportFormat.OFF,
        }
    )
    # Its STEP writer declares no unit; only 3MF states millimeters.
    unit_recording_formats: ClassVar[frozenset[ExportFormat]] = frozenset({ExportFormat.THREE_MF})

    def __init__(self, native: "PyOpenSCAD", coordinate_system: CartesianCoordinateSystem) -> None:
        super().__init__(coordinate_system)
        self._native: PyOpenSCAD = native

    @property
    def native(self) -> "PyOpenSCAD":
        """The wrapped PythonSCAD object."""
        return self._native

    def _wrap(self, native: "PyOpenSCAD") -> Self:
        return type(self)(native, self.coordinate_system)

    @override
    def _with_coordinate_system(self, coordinate_system: CartesianCoordinateSystem) -> Self:
        return type(self)(self._native, coordinate_system)

    @override
    def _bounds(self) -> tuple[Vector3, Vector3]:
        points, _ = self._native.mesh()
        if not points:
            raise EmptySolidError("The PythonSCAD solid has no volume.")
        coordinates = np.asarray(points, dtype=np.float64)
        x_min, y_min, z_min = (float(value) for value in coordinates.min(axis=0))
        x_max, y_max, z_max = (float(value) for value in coordinates.max(axis=0))
        return (x_min, y_min, z_min), (x_max, y_max, z_max)

    @override
    def _union(self, other: Solid) -> Self:
        return self._wrap(self._native.union(self._as_same_backend(other)._native))

    @override
    def _difference(self, other: Solid) -> Self:
        return self._wrap(self._native.difference(self._as_same_backend(other)._native))

    @override
    def _intersection(self, other: Solid) -> Self:
        return self._wrap(self._native.intersection(self._as_same_backend(other)._native))

    @override
    def _translate(self, offset: Vector3) -> Self:
        return self._wrap(self._native.translate(list(offset)))

    @override
    def _rotate(self, axis: Axis, degrees: float) -> Self:
        angles = [0.0, 0.0, 0.0]
        angles[axis.to_index] = degrees
        return self._wrap(self._native.rotate(angles))

    @override
    def _scale(self, factors: Vector3) -> Self:
        return self._wrap(self._native.scale(list(factors)))

    @override
    def _mirror(self, normal: Vector3) -> Self:
        return self._wrap(self._native.mirror(list(normal)))

    @override
    def _export(self, path: Path, export_format: ExportFormat) -> None:
        # PythonSCAD picks the format from the suffix itself; Solid.export has already validated it.
        self._native.export(str(path))
