from dataclasses import dataclass
from typing import override

import openscad
from cartesian_axis import CartesianCoordinateSystem

from ..modeler import Modeler
from ..profile import Loop
from ..vector import Vector3
from .solid import PythonSCADSolid


@dataclass(frozen=True)
class PythonSCADModeler(Modeler[PythonSCADSolid]):
    """
    Creates primitives with PythonSCAD.

    Parameters
    ----------
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the created solids are expressed in.
    segment_count : int
        Number of line segments approximating a full circle in cylinders and
        spheres (OpenSCAD's ``$fn``). Higher values give smoother meshes.

    Raises
    ------
    ValueError
        If ``segment_count`` is less than 3.
    """

    segment_count: int = 64

    def __post_init__(self) -> None:
        if self.segment_count < 3:
            raise ValueError(f"segment_count must be at least 3, got {self.segment_count}.")

    @override
    def _box(self, size: Vector3, is_centered: bool) -> PythonSCADSolid:
        return PythonSCADSolid(
            openscad.cube(list(size), center=is_centered), self.coordinate_system
        )

    @override
    def _cylinder(self, radius: float, height: float, is_centered: bool) -> PythonSCADSolid:
        return PythonSCADSolid(
            openscad.cylinder(r=radius, h=height, center=is_centered, fn=self.segment_count),
            self.coordinate_system,
        )

    @override
    def _sphere(self, radius: float) -> PythonSCADSolid:
        return PythonSCADSolid(
            openscad.sphere(r=radius, fn=self.segment_count), self.coordinate_system
        )

    @override
    def _prism(
        self, loop: Loop, height: float, coordinate_system: CartesianCoordinateSystem
    ) -> PythonSCADSolid:
        polygon = openscad.polygon(loop.tolist())
        return PythonSCADSolid(openscad.linear_extrude(polygon, height=height), coordinate_system)
