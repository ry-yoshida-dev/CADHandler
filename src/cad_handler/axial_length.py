from dataclasses import dataclass
from typing import Self, override

import numpy as np
from cartesian_axis import Axis
from units import Length, LengthUnit, MetricPrefix

from .scalar import single_finite_value

# Matches the relative tolerance `units` uses to compare quantities.
_EQUALITY_TOLERANCE: float = 1e-9


@dataclass(frozen=True, eq=False)
class AxialLength:
    """
    Length along one coordinate axis, in its positive or negative direction.

    ``units.Length`` holds only magnitudes, so the direction is kept apart from
    it. A zero length has no direction: it equals its negation.

    Parameters
    ----------
    magnitude : Length
        Distance along the axis, as a single value.
    axis : Axis
        Axis the length runs along.
    is_negative : bool
        Whether the length points toward the negative side of ``axis``.

    Raises
    ------
    ValueError
        If ``magnitude`` does not hold exactly one finite value.
    """

    magnitude: Length
    axis: Axis
    is_negative: bool = False

    def __post_init__(self) -> None:
        single_finite_value("magnitude", self.magnitude.value)

    @classmethod
    def from_signed_value(
        cls,
        value: float,
        unit: LengthUnit,
        axis: Axis,
        prefix: MetricPrefix = MetricPrefix.NONE,
    ) -> Self:
        """
        Build a length from a signed number in a unit.

        Parameters
        ----------
        value : float
            Signed length; negative values point toward the negative side of ``axis``.
        unit : LengthUnit
            Unit of ``value``.
        axis : Axis
            Axis the length runs along.
        prefix : MetricPrefix
            Prefix of ``unit``, or ``MetricPrefix.NONE`` for the unit itself.

        Returns
        -------
        Self
            The axial length, keeping ``unit`` and ``prefix``.

        Raises
        ------
        ValueError
            If ``value`` is not finite, or ``unit`` takes no prefix but one is given.
        """
        magnitude = Length(value=np.array([abs(value)]), unit=unit, prefix=prefix)
        return cls(magnitude=magnitude, axis=axis, is_negative=value < 0)

    def signed_value(self, unit: LengthUnit, prefix: MetricPrefix = MetricPrefix.NONE) -> float:
        """
        Express the length as a signed number.

        Parameters
        ----------
        unit : LengthUnit
            Unit to express the length in.
        prefix : MetricPrefix
            Prefix of ``unit``, or ``MetricPrefix.NONE`` for the unit itself.

        Returns
        -------
        float
            The length, negative when it points toward the negative side of the axis.

        Raises
        ------
        ValueError
            If ``unit`` takes no prefix but one is given.
        """
        value = float(self.magnitude.in_unit(unit, prefix).item())
        return -value if self.is_negative else value

    def __neg__(self) -> Self:
        """Reverse the direction, keeping the magnitude and axis."""
        return type(self)(
            magnitude=self.magnitude, axis=self.axis, is_negative=not self.is_negative
        )

    @override
    def __eq__(self, other: object) -> bool:
        """Compare axis and signed length, within the tolerance ``units`` uses."""
        if not isinstance(other, AxialLength):
            return NotImplemented
        absolute_tolerance = _EQUALITY_TOLERANCE * min(
            self.magnitude.unit.scale(self.magnitude.prefix),
            other.magnitude.unit.scale(other.magnitude.prefix),
        )
        return self.axis is other.axis and bool(
            np.isclose(
                self.signed_value(LengthUnit.M),
                other.signed_value(LengthUnit.M),
                rtol=_EQUALITY_TOLERANCE,
                atol=absolute_tolerance,
            )
        )

    @override
    def __repr__(self) -> str:
        sign = "-" if self.is_negative else "+"
        return f"AxialLength({sign}{self.magnitude} along {self.axis.value})"
