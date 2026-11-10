import math
from abc import ABC, abstractmethod

from .solid import Solid
from .vector import Vector3


class Modeler[SolidT: Solid](ABC):
    """
    Creates primitive solids of one CAD backend.

    Primitives are placed relative to the origin: centered ones have their
    center there, the others have their minimum corner (box) or base center
    (cylinder) there.
    """

    def box(self, size: Vector3, is_centered: bool = False) -> SolidT:
        """
        Create an axis-aligned box.

        Parameters
        ----------
        size : Vector3
            Edge length along x, y, and z.
        is_centered : bool
            Center the box on the origin instead of putting its minimum corner there.

        Returns
        -------
        SolidT
            The box.

        Raises
        ------
        ValueError
            If an edge length is not finite or not positive.
        """
        for axis, length in zip("xyz", size, strict=True):
            _validate_positive(f"size along {axis}", length)
        return self._box(size, is_centered)

    def cylinder(self, radius: float, height: float, is_centered: bool = False) -> SolidT:
        """
        Create a cylinder along the z axis.

        Parameters
        ----------
        radius : float
            Radius of the circular cross-section.
        height : float
            Length along z.
        is_centered : bool
            Center the cylinder on the origin instead of putting its base there.

        Returns
        -------
        SolidT
            The cylinder.

        Raises
        ------
        ValueError
            If ``radius`` or ``height`` is not finite or not positive.
        """
        _validate_positive("radius", radius)
        _validate_positive("height", height)
        return self._cylinder(radius, height, is_centered)

    def sphere(self, radius: float) -> SolidT:
        """
        Create a sphere centered on the origin.

        Parameters
        ----------
        radius : float
            Radius of the sphere.

        Returns
        -------
        SolidT
            The sphere.

        Raises
        ------
        ValueError
            If ``radius`` is not finite or not positive.
        """
        _validate_positive("radius", radius)
        return self._sphere(radius)

    @abstractmethod
    def _box(self, size: Vector3, is_centered: bool) -> SolidT: ...

    @abstractmethod
    def _cylinder(self, radius: float, height: float, is_centered: bool) -> SolidT: ...

    @abstractmethod
    def _sphere(self, radius: float) -> SolidT: ...


def _validate_positive(name: str, value: float) -> None:
    if not (math.isfinite(value) and value > 0):
        raise ValueError(f"{name} must be finite and positive, got {value}.")
