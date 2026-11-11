from dataclasses import dataclass
from typing import override

from cadquery import Face, Vector, Wire
from cadquery import Solid as CadQueryShapeSolid
from cartesian_axis import CartesianCoordinateSystem

from ..modeler import Modeler
from ..profile import Loop
from ..vector import Vector3
from .solid import CadQuerySolid


@dataclass(frozen=True)
class CadQueryModeler(Modeler[CadQuerySolid]):
    """
    Creates exact boundary-representation primitives with CadQuery.

    Parameters
    ----------
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the created solids are expressed in.
    """

    @override
    def _box(self, size: Vector3, is_centered: bool) -> CadQuerySolid:
        length, width, height = size
        corner = (-length / 2, -width / 2, -height / 2) if is_centered else (0.0, 0.0, 0.0)
        return CadQuerySolid(
            CadQueryShapeSolid.makeBox(length, width, height, pnt=corner), self.coordinate_system
        )

    @override
    def _cylinder(self, radius: float, height: float, is_centered: bool) -> CadQuerySolid:
        base_center = (0.0, 0.0, -height / 2 if is_centered else 0.0)
        return CadQuerySolid(
            CadQueryShapeSolid.makeCylinder(radius, height, pnt=base_center), self.coordinate_system
        )

    @override
    def _sphere(self, radius: float) -> CadQuerySolid:
        # makeSphere defaults to the upper hemisphere; -90 to 90 degrees spans the full sphere.
        return CadQuerySolid(
            CadQueryShapeSolid.makeSphere(radius, angleDegrees1=-90, angleDegrees2=90),
            self.coordinate_system,
        )

    @override
    def _prism(
        self, loop: Loop, height: float, coordinate_system: CartesianCoordinateSystem
    ) -> CadQuerySolid:
        wire = Wire.makePolygon([Vector(float(x), float(y), 0.0) for x, y in loop], close=True)
        return CadQuerySolid(
            CadQueryShapeSolid.extrudeLinear(Face.makeFromWires(wire), Vector(0.0, 0.0, height)),
            coordinate_system,
        )
