from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Self, override

import numpy as np

from ..bounding_box import BoundingBox
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

    def __init__(self, native: "PyOpenSCAD") -> None:
        self._native: PyOpenSCAD = native

    @property
    def native(self) -> "PyOpenSCAD":
        """The wrapped PythonSCAD object."""
        return self._native

    @property
    @override
    def bounding_box(self) -> BoundingBox:
        points, _ = self._native.mesh()
        if not points:
            raise EmptySolidError("The PythonSCAD solid has no volume.")
        coordinates = np.asarray(points, dtype=np.float64)
        x_min, y_min, z_min = (float(value) for value in coordinates.min(axis=0))
        x_max, y_max, z_max = (float(value) for value in coordinates.max(axis=0))
        return BoundingBox(minimum=(x_min, y_min, z_min), maximum=(x_max, y_max, z_max))

    @override
    def _union(self, other: Solid) -> Self:
        return type(self)(self._native.union(self._as_same_backend(other)._native))

    @override
    def _difference(self, other: Solid) -> Self:
        return type(self)(self._native.difference(self._as_same_backend(other)._native))

    @override
    def _intersection(self, other: Solid) -> Self:
        return type(self)(self._native.intersection(self._as_same_backend(other)._native))

    @override
    def _translate(self, offset: Vector3) -> Self:
        return type(self)(self._native.translate(list(offset)))

    @override
    def _rotate(self, angles: Vector3) -> Self:
        return type(self)(self._native.rotate(list(angles)))

    @override
    def _scale(self, factors: Vector3) -> Self:
        return type(self)(self._native.scale(list(factors)))

    @override
    def _mirror(self, normal: Vector3) -> Self:
        return type(self)(self._native.mirror(list(normal)))

    @override
    def _export(self, path: Path, export_format: ExportFormat) -> None:
        # PythonSCAD picks the format from the suffix itself; Solid.export has already validated it.
        self._native.export(str(path))
