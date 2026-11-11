import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Self

from cartesian_axis import Axis, CartesianCoordinateSystem
from units import Angle, Length

from .axis_conversion import AxisConversion
from .bounding_box import BoundingBox
from .displacement import Displacement
from .errors import (
    CoordinateSystemMismatchError,
    CoordinateUnitRequiredError,
    UnsupportedExportFormatError,
)
from .export_format import ExportFormat
from .kernel_unit import (
    KERNEL_LENGTH_PREFIX,
    KERNEL_LENGTH_UNIT,
    to_kernel_degrees,
    to_kernel_length,
)
from .vector import Vector3


class Solid(ABC):
    """
    Immutable 3D solid of one CAD backend.

    Every operation returns a new solid and leaves the receiver unchanged.
    Coordinates, offsets, and axes are read in the solid's coordinate system,
    and ``to_coordinate_system`` re-expresses the solid in another one.
    Boolean operations combine only solids of the same backend and coordinate
    system; ``|``, ``-``, and ``&`` are shorthands for ``union``,
    ``difference``, and ``intersection``.

    Parameters
    ----------
    coordinate_system : CartesianCoordinateSystem
        Coordinate system the solid's geometry is expressed in.
    """

    backend_name: ClassVar[str]
    """Human-readable backend name used in error messages."""

    supported_export_formats: ClassVar[frozenset[ExportFormat]]
    """Formats ``export`` can write with this backend."""

    unit_recording_formats: ClassVar[frozenset[ExportFormat]]
    """Supported formats whose files this backend writes with a length unit (millimeters)."""

    def __init__(self, coordinate_system: CartesianCoordinateSystem) -> None:
        self._coordinate_system: CartesianCoordinateSystem = coordinate_system

    @property
    def coordinate_system(self) -> CartesianCoordinateSystem:
        """Coordinate system the solid's geometry is expressed in."""
        return self._coordinate_system

    def to_coordinate_system(self, target: CartesianCoordinateSystem) -> Self:
        """
        Express the solid in another coordinate system.

        The values along each role (forward, right, and up) move to the
        target's axis for that role, as ``cartesian_axis`` converts
        coordinates. When the axes are permuted oddly, the result is the
        mirror image of the original.

        Parameters
        ----------
        target : CartesianCoordinateSystem
            Coordinate system to express the solid in.

        Returns
        -------
        Self
            The solid in ``target``.
        """
        conversion = AxisConversion.between(self._coordinate_system, target)
        converted = self._mirror((0.0, 0.0, 1.0)) if conversion.is_mirrored else self
        for axis, turns in zip(Axis, conversion.quarter_turns, strict=True):
            if turns:
                converted = converted._rotate(axis, 90.0 * turns)
        return converted._with_coordinate_system(target)

    @property
    def bounding_box(self) -> BoundingBox:
        """
        Axis-aligned box enclosing the solid.

        Raises
        ------
        EmptySolidError
            If the solid has no volume.
        """
        minimum, maximum = self._bounds()
        return BoundingBox(
            minimum=Displacement.from_signed_values(
                minimum, KERNEL_LENGTH_UNIT, KERNEL_LENGTH_PREFIX
            ),
            maximum=Displacement.from_signed_values(
                maximum, KERNEL_LENGTH_UNIT, KERNEL_LENGTH_PREFIX
            ),
        )

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
        CoordinateSystemMismatchError
            If ``other`` is expressed in a different coordinate system.
        """
        self._validate_same_coordinate_system(other)
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
        CoordinateSystemMismatchError
            If ``other`` is expressed in a different coordinate system.
        """
        self._validate_same_coordinate_system(other)
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
        CoordinateSystemMismatchError
            If ``other`` is expressed in a different coordinate system.
        """
        self._validate_same_coordinate_system(other)
        return self._intersection(other)

    def translate(self, offset: Displacement) -> Self:
        """
        Move the solid.

        Parameters
        ----------
        offset : Displacement
            Displacement to move by.

        Returns
        -------
        Self
            The moved solid.
        """
        return self._translate(offset.signed_values(KERNEL_LENGTH_UNIT, KERNEL_LENGTH_PREFIX))

    def rotate(self, axis: Axis, angle: Angle) -> Self:
        """
        Rotate the solid about a coordinate axis through the origin.

        Chain calls to rotate about several axes; each turn applies to the
        result of the previous one.

        Parameters
        ----------
        axis : Axis
            Axis to rotate about.
        angle : Angle
            Rotation angle as a single value. Positive angles turn +y toward
            +z about x, +z toward +x about y, and +x toward +y about z. Seen
            from the positive side of ``axis``, that is counterclockwise in a
            right-handed coordinate system and clockwise in a left-handed one.

        Returns
        -------
        Self
            The rotated solid.

        Raises
        ------
        ValueError
            If ``angle`` is not a single finite value.
        """
        return self._rotate(axis, to_kernel_degrees("angle", angle))

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

    def export(self, path: Path, coordinate_unit: Length | None = None) -> None:
        """
        Write the solid to a file whose format is inferred from the suffix.

        Formats in ``unit_recording_formats`` state their unit in the file.
        For the others the file holds bare numbers, so the length one number
        stands for must be given.

        Parameters
        ----------
        path : Path
            Destination file. Its parent directory must exist.
        coordinate_unit : Length | None
            Length one coordinate in the file stands for, such as 1 mm or
            1 inch. Required for formats that record no unit, and ``None`` for
            those that do.

        Raises
        ------
        ValueError
            If the suffix matches no ``ExportFormat``, ``coordinate_unit`` is
            given for a format that records its unit, or ``coordinate_unit`` is
            not a single finite, positive value.
        UnsupportedExportFormatError
            If this backend cannot write the format.
        CoordinateUnitRequiredError
            If the format records no unit and ``coordinate_unit`` is ``None``.
        FileNotFoundError
            If the parent directory does not exist.
        """
        export_format = ExportFormat.from_path(path)
        if export_format not in self.supported_export_formats:
            raise UnsupportedExportFormatError(
                export_format, self.backend_name, self.supported_export_formats
            )
        is_unit_recorded = export_format in self.unit_recording_formats
        if is_unit_recorded and coordinate_unit is not None:
            raise ValueError(
                f"{self.backend_name} records the unit of {export_format.name} files itself; "
                + "coordinate_unit applies only to formats without one."
            )
        if not is_unit_recorded and coordinate_unit is None:
            raise CoordinateUnitRequiredError(export_format, self.backend_name)
        if not path.parent.is_dir():
            raise FileNotFoundError(f"Parent directory of {path} does not exist.")
        if coordinate_unit is None:
            self._export(path, export_format)
            return
        unit_in_kernel = to_kernel_length("coordinate_unit", coordinate_unit)
        if unit_in_kernel <= 0:
            raise ValueError(f"coordinate_unit must be positive, got {coordinate_unit}.")
        factor = 1.0 / unit_in_kernel
        self._scale((factor, factor, factor))._export(path, export_format)

    def __or__(self, other: Self) -> Self:
        return self.union(other)

    def __sub__(self, other: Self) -> Self:
        return self.difference(other)

    def __and__(self, other: Self) -> Self:
        return self.intersection(other)

    def _validate_same_coordinate_system(self, other: "Solid") -> None:
        if other.coordinate_system != self._coordinate_system:
            raise CoordinateSystemMismatchError(self._coordinate_system, other.coordinate_system)

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
    def _with_coordinate_system(self, coordinate_system: CartesianCoordinateSystem) -> Self: ...

    @abstractmethod
    def _bounds(self) -> tuple[Vector3, Vector3]: ...

    @abstractmethod
    def _translate(self, offset: Vector3) -> Self: ...

    @abstractmethod
    def _rotate(self, axis: Axis, degrees: float) -> Self: ...

    @abstractmethod
    def _scale(self, factors: Vector3) -> Self: ...

    @abstractmethod
    def _mirror(self, normal: Vector3) -> Self: ...

    @abstractmethod
    def _export(self, path: Path, export_format: ExportFormat) -> None: ...


def _validate_finite(name: str, vector: Vector3) -> None:
    if not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{name} must be finite, got {vector}.")
