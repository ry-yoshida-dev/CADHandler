from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from cartesian_axis import Axis, CartesianCoordinateSystem
from units import Angle, AngleUnit, Length

from .kernel_unit import KERNEL_LENGTH_PREFIX, KERNEL_LENGTH_UNIT, to_kernel_length
from .profile import Loop, Profile
from .solid import Solid
from .vector import Vector3

# Turns a cylinder built along z onto the requested axis; z needs no turn.
_QUARTER_TURN: Angle = Angle(value=np.array([90.0]), unit=AngleUnit.DEGREE)


@dataclass(frozen=True)
class Modeler[SolidT: Solid](ABC):
    """
    Creates primitive solids of one CAD backend in a coordinate system.

    Primitives are placed relative to the origin: centered ones have their
    center there, the others have their minimum corner (box) or base center
    (cylinder) there. Their axes are those of ``coordinate_system``.

    Parameters
    ----------
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the created solids are expressed in.
    """

    coordinate_system: CartesianCoordinateSystem

    def box(self, x: Length, y: Length, z: Length, is_centered: bool = False) -> SolidT:
        """
        Create an axis-aligned box.

        Parameters
        ----------
        x : Length
            Edge length along x.
        y : Length
            Edge length along y.
        z : Length
            Edge length along z.
        is_centered : bool
            Center the box on the origin instead of putting its minimum corner there.

        Returns
        -------
        SolidT
            The box.

        Raises
        ------
        ValueError
            If an edge length is not a single finite, positive value.
        """
        size = (
            _to_positive_kernel_length("x", x),
            _to_positive_kernel_length("y", y),
            _to_positive_kernel_length("z", z),
        )
        return self._box(size, is_centered)

    def cylinder(
        self, radius: Length, height: Length, axis: Axis, is_centered: bool = False
    ) -> SolidT:
        """
        Create a cylinder along a coordinate axis.

        Parameters
        ----------
        radius : Length
            Radius of the circular cross-section.
        height : Length
            Length along ``axis``.
        axis : Axis
            Axis the cylinder runs along, from its base toward the positive side.
        is_centered : bool
            Center the cylinder on the origin instead of putting its base there.

        Returns
        -------
        SolidT
            The cylinder.

        Raises
        ------
        ValueError
            If ``radius`` or ``height`` is not a single finite, positive value.
        """
        along_z = self._cylinder(
            _to_positive_kernel_length("radius", radius),
            _to_positive_kernel_length("height", height),
            is_centered,
        )
        match axis:
            case Axis.X:
                return along_z.rotate(Axis.Y, _QUARTER_TURN)
            case Axis.Y:
                return along_z.rotate(Axis.X, -_QUARTER_TURN)
            case Axis.Z:
                return along_z

    def sphere(self, radius: Length) -> SolidT:
        """
        Create a sphere centered on the origin.

        Parameters
        ----------
        radius : Length
            Radius of the sphere.

        Returns
        -------
        SolidT
            The sphere.

        Raises
        ------
        ValueError
            If ``radius`` is not a single finite, positive value.
        """
        return self._sphere(_to_positive_kernel_length("radius", radius))

    def extrude(self, profile: Profile, height: Length) -> SolidT:
        """
        Extrude a planar profile from its xy plane toward its positive z.

        The extrusion is built in the profile's coordinate system and then
        expressed in this modeler's with ``Solid.to_coordinate_system``.

        Parameters
        ----------
        profile : Profile
            Region to extrude; holes and islands follow its nesting.
        height : Length
            Extrusion distance.

        Returns
        -------
        SolidT
            The extruded solid in this modeler's coordinate system.

        Raises
        ------
        ValueError
            If ``height`` is not a single finite, positive value.
        """
        kernel_height = _to_positive_kernel_length("height", height)
        loops = profile.loops_in(KERNEL_LENGTH_UNIT, KERNEL_LENGTH_PREFIX)
        depths = profile.nesting_depths
        # Shallower loops enclose deeper ones, so adding and cutting by depth follows the even-odd rule.
        first, *rest = sorted(range(len(loops)), key=depths.__getitem__)
        system = profile.coordinate_system
        solid = self._prism(loops[first], kernel_height, system)
        for index in rest:
            prism = self._prism(loops[index], kernel_height, system)
            solid = solid.difference(prism) if depths[index] % 2 else solid.union(prism)
        return solid.to_coordinate_system(self.coordinate_system)

    @abstractmethod
    def _box(self, size: Vector3, is_centered: bool) -> SolidT: ...

    @abstractmethod
    def _cylinder(self, radius: float, height: float, is_centered: bool) -> SolidT: ...

    @abstractmethod
    def _sphere(self, radius: float) -> SolidT: ...

    @abstractmethod
    def _prism(
        self, loop: Loop, height: float, coordinate_system: CartesianCoordinateSystem
    ) -> SolidT: ...


def _to_positive_kernel_length(name: str, length: Length) -> float:
    value = to_kernel_length(name, length)
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {length}.")
    return value
