from typing import override

from cadquery import Solid as CadQueryShapeSolid

from ..modeler import Modeler
from ..vector import Vector3
from .solid import CadQuerySolid


class CadQueryModeler(Modeler[CadQuerySolid]):
    """Creates exact boundary-representation primitives with CadQuery."""

    @override
    def _box(self, size: Vector3, is_centered: bool) -> CadQuerySolid:
        length, width, height = size
        corner = (-length / 2, -width / 2, -height / 2) if is_centered else (0.0, 0.0, 0.0)
        return CadQuerySolid(CadQueryShapeSolid.makeBox(length, width, height, pnt=corner))

    @override
    def _cylinder(self, radius: float, height: float, is_centered: bool) -> CadQuerySolid:
        base_center = (0.0, 0.0, -height / 2 if is_centered else 0.0)
        return CadQuerySolid(CadQueryShapeSolid.makeCylinder(radius, height, pnt=base_center))

    @override
    def _sphere(self, radius: float) -> CadQuerySolid:
        # makeSphere defaults to the upper hemisphere; -90 to 90 degrees spans the full sphere.
        return CadQuerySolid(
            CadQueryShapeSolid.makeSphere(radius, angleDegrees1=-90, angleDegrees2=90)
        )
