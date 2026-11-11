from dataclasses import dataclass

import numpy as np
from cartesian_axis import Axis
from units import Length, LengthUnit

from .displacement import Displacement


@dataclass(frozen=True)
class BoundingBox:
    """
    Axis-aligned box enclosing a solid.

    Parameters
    ----------
    minimum : Displacement
        Position of the corner with the smallest x, y, and z.
    maximum : Displacement
        Position of the corner with the largest x, y, and z.

    Raises
    ------
    ValueError
        If any coordinate of ``minimum`` exceeds that of ``maximum``.
    """

    minimum: Displacement
    maximum: Displacement

    def __post_init__(self) -> None:
        lows = self.minimum.signed_values(LengthUnit.M)
        highs = self.maximum.signed_values(LengthUnit.M)
        if any(low > high for low, high in zip(lows, highs, strict=True)):
            raise ValueError(
                f"minimum {self.minimum} must not exceed maximum {self.maximum} on any axis."
            )

    def extent(self, axis: Axis) -> Length:
        """
        Get the size of the box along an axis.

        Parameters
        ----------
        axis : Axis
            The axis.

        Returns
        -------
        Length
            Distance between the two corners along ``axis``, in meters.
        """
        low = self.minimum.along(axis).signed_value(LengthUnit.M)
        high = self.maximum.along(axis).signed_value(LengthUnit.M)
        return Length(value=np.array([high - low]), unit=LengthUnit.M)

    @property
    def center(self) -> Displacement:
        """Position of the midpoint between the two corners, in meters."""
        lows = self.minimum.signed_values(LengthUnit.M)
        highs = self.maximum.signed_values(LengthUnit.M)
        x, y, z = ((low + high) / 2 for low, high in zip(lows, highs, strict=True))
        return Displacement.from_signed_values((x, y, z), LengthUnit.M)
