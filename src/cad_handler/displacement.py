from dataclasses import dataclass
from typing import Self, override

from cartesian_axis import Axis
from units import LengthUnit, MetricPrefix

from .axial_length import AxialLength
from .vector import Vector3

# Sums and differences are expressed in meters, the base unit of `units.Length`.
_SUM_UNIT: LengthUnit = LengthUnit.M


@dataclass(frozen=True, eq=False)
class Displacement:
    """
    Offset in 3D space, made of at most one length along each axis.

    Axes without a component are zero. A position is the displacement from the
    origin. Components are read in the coordinate system of the solid they are
    applied to.

    Parameters
    ----------
    components : tuple[AxialLength, ...]
        Lengths along distinct axes.

    Raises
    ------
    ValueError
        If two components run along the same axis.
    """

    components: tuple[AxialLength, ...] = ()

    def __post_init__(self) -> None:
        axes = [component.axis for component in self.components]
        if len(set(axes)) != len(axes):
            names = ", ".join(axis.value for axis in axes)
            raise ValueError(f"components must run along distinct axes, got {names}.")

    @classmethod
    def of(cls, *components: AxialLength) -> Self:
        """
        Build a displacement from its components.

        Parameters
        ----------
        *components : AxialLength
            Lengths along distinct axes; omitted axes are zero.

        Returns
        -------
        Self
            The displacement.

        Raises
        ------
        ValueError
            If two components run along the same axis.
        """
        return cls(components=components)

    @classmethod
    def from_signed_values(
        cls, values: Vector3, unit: LengthUnit, prefix: MetricPrefix = MetricPrefix.NONE
    ) -> Self:
        """
        Build a displacement from signed numbers along x, y, and z.

        Parameters
        ----------
        values : Vector3
            Signed lengths along x, y, and z.
        unit : LengthUnit
            Unit of ``values``.
        prefix : MetricPrefix
            Prefix of ``unit``, or ``MetricPrefix.NONE`` for the unit itself.

        Returns
        -------
        Self
            The displacement with a component on every axis.

        Raises
        ------
        ValueError
            If a value is not finite, or ``unit`` takes no prefix but one is given.
        """
        return cls(
            components=tuple(
                AxialLength.from_signed_value(value, unit, axis, prefix)
                for axis, value in zip(Axis, values, strict=True)
            )
        )

    def along(self, axis: Axis) -> AxialLength:
        """
        Get the component along an axis.

        Parameters
        ----------
        axis : Axis
            The axis.

        Returns
        -------
        AxialLength
            The component, or a zero length when the axis has none.
        """
        for component in self.components:
            if component.axis is axis:
                return component
        return AxialLength.from_signed_value(0.0, _SUM_UNIT, axis)

    def signed_values(self, unit: LengthUnit, prefix: MetricPrefix = MetricPrefix.NONE) -> Vector3:
        """
        Express the displacement as signed numbers along x, y, and z.

        Parameters
        ----------
        unit : LengthUnit
            Unit to express the components in.
        prefix : MetricPrefix
            Prefix of ``unit``, or ``MetricPrefix.NONE`` for the unit itself.

        Returns
        -------
        Vector3
            Signed lengths along x, y, and z.

        Raises
        ------
        ValueError
            If ``unit`` takes no prefix but one is given.
        """
        x, y, z = (self.along(axis).signed_value(unit, prefix) for axis in Axis)
        return (x, y, z)

    def __add__(self, other: Self) -> Self:
        """Add component-wise; the result is in meters."""
        sums = zip(self.signed_values(_SUM_UNIT), other.signed_values(_SUM_UNIT), strict=True)
        x, y, z = (first + second for first, second in sums)
        return type(self).from_signed_values((x, y, z), _SUM_UNIT)

    def __sub__(self, other: Self) -> Self:
        """Subtract component-wise; the result is in meters."""
        return self + -other

    def __neg__(self) -> Self:
        """Reverse every component."""
        return type(self)(components=tuple(-component for component in self.components))

    @override
    def __eq__(self, other: object) -> bool:
        """Compare every axis, treating missing components as zero."""
        if not isinstance(other, Displacement):
            return NotImplemented
        return all(self.along(axis) == other.along(axis) for axis in Axis)
