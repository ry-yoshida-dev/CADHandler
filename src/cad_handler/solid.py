import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Self

from .bounding_box import BoundingBox
from .errors import UnsupportedExportFormatError
from .export_format import ExportFormat
from .vector import Vector3


class Solid(ABC):
    """
    Immutable 3D solid of one CAD backend.

    Every operation returns a new solid and leaves the receiver unchanged.
    Boolean operations combine only solids of the same backend; ``|``, ``-``,
    and ``&`` are shorthands for ``union``, ``difference``, and ``intersection``.
    """

    backend_name: ClassVar[str]
    """Human-readable backend name used in error messages."""

    supported_export_formats: ClassVar[frozenset[ExportFormat]]
    """Formats ``export`` can write with this backend."""

    @property
    @abstractmethod
    def bounding_box(self) -> BoundingBox:
        """
        Axis-aligned box enclosing the solid.

        Raises
        ------
        EmptySolidError
            If the solid has no volume.
        """

    def union(self, other: Self) -> Self:
        """
        Combine this solid with another.

        Parameters
        ----------
        other : Self
            Solid of the same backend.

        Returns
        -------
        Self
            Volume covered by either solid.

        Raises
        ------
        TypeError
            If ``other`` belongs to a different backend.
        """
        return self._union(other)

    def difference(self, other: Self) -> Self:
        """
        Subtract another solid from this one.

        Parameters
        ----------
        other : Self
            Solid of the same backend to cut away.

        Returns
        -------
        Self
            Volume of this solid not covered by ``other``.

        Raises
        ------
        TypeError
            If ``other`` belongs to a different backend.
        """
        return self._difference(other)

    def intersection(self, other: Self) -> Self:
        """
        Keep only the volume shared with another solid.

        Parameters
        ----------
        other : Self
            Solid of the same backend.

        Returns
        -------
        Self
            Volume covered by both solids.

        Raises
        ------
        TypeError
            If ``other`` belongs to a different backend.
        """
        return self._intersection(other)

    def translate(self, offset: Vector3) -> Self:
        """
        Move the solid.

        Parameters
        ----------
        offset : Vector3
            Displacement along x, y, and z.

        Returns
        -------
        Self
            The moved solid.

        Raises
        ------
        ValueError
            If ``offset`` contains a non-finite value.
        """
        _validate_finite("offset", offset)
        return self._translate(offset)

    def rotate(self, angles: Vector3) -> Self:
        """
        Rotate the solid about the origin.

        Parameters
        ----------
        angles : Vector3
            Angles in degrees about the x, y, and z axes, applied in that order
            (the OpenSCAD ``rotate([x, y, z])`` convention). Positive angles turn
            counterclockwise when looking from the positive axis toward the origin.

        Returns
        -------
        Self
            The rotated solid.

        Raises
        ------
        ValueError
            If ``angles`` contains a non-finite value.
        """
        _validate_finite("angles", angles)
        return self._rotate(angles)

    def scale(self, factors: Vector3) -> Self:
        """
        Scale the solid about the origin.

        Parameters
        ----------
        factors : Vector3
            Scale factor along x, y, and z.

        Returns
        -------
        Self
            The scaled solid.

        Raises
        ------
        ValueError
            If a factor is not finite or not positive.
        """
        _validate_finite("factors", factors)
        if any(factor <= 0 for factor in factors):
            raise ValueError(f"factors must be positive, got {factors}.")
        return self._scale(factors)

    def mirror(self, normal: Vector3) -> Self:
        """
        Reflect the solid across a plane through the origin.

        Parameters
        ----------
        normal : Vector3
            Normal vector of the mirror plane; its length does not matter.

        Returns
        -------
        Self
            The reflected solid.

        Raises
        ------
        ValueError
            If ``normal`` contains a non-finite value or is the zero vector.
        """
        _validate_finite("normal", normal)
        if all(component == 0 for component in normal):
            raise ValueError("normal must not be the zero vector.")
        return self._mirror(normal)

    def export(self, path: Path) -> None:
        """
        Write the solid to a file whose format is inferred from the suffix.

        Parameters
        ----------
        path : Path
            Destination file. Its parent directory must exist.

        Raises
        ------
        ValueError
            If the suffix matches no ``ExportFormat``.
        UnsupportedExportFormatError
            If this backend cannot write the format.
        FileNotFoundError
            If the parent directory does not exist.
        """
        export_format = ExportFormat.from_path(path)
        if export_format not in self.supported_export_formats:
            raise UnsupportedExportFormatError(
                export_format, self.backend_name, self.supported_export_formats
            )
        if not path.parent.is_dir():
            raise FileNotFoundError(f"Parent directory of {path} does not exist.")
        self._export(path, export_format)

    def __or__(self, other: Self) -> Self:
        return self.union(other)

    def __sub__(self, other: Self) -> Self:
        return self.difference(other)

    def __and__(self, other: Self) -> Self:
        return self.intersection(other)

    def _as_same_backend(self, other: "Solid") -> Self:
        """Narrow ``other`` to this backend; backends call it before touching ``other``'s native object."""
        # Self only protects callers holding a concrete type; code typed against Solid can still mix backends.
        if not isinstance(other, type(self)):
            raise TypeError(
                f"Cannot combine {type(self).__name__} with {type(other).__name__}; both solids must come from the same backend."
            )
        return other

    # Boolean hooks take Solid rather than Self because type checkers reject overriding a Self parameter.
    @abstractmethod
    def _union(self, other: "Solid") -> Self: ...

    @abstractmethod
    def _difference(self, other: "Solid") -> Self: ...

    @abstractmethod
    def _intersection(self, other: "Solid") -> Self: ...

    @abstractmethod
    def _translate(self, offset: Vector3) -> Self: ...

    @abstractmethod
    def _rotate(self, angles: Vector3) -> Self: ...

    @abstractmethod
    def _scale(self, factors: Vector3) -> Self: ...

    @abstractmethod
    def _mirror(self, normal: Vector3) -> Self: ...

    @abstractmethod
    def _export(self, path: Path, export_format: ExportFormat) -> None: ...


def _validate_finite(name: str, vector: Vector3) -> None:
    if not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{name} must be finite, got {vector}.")
