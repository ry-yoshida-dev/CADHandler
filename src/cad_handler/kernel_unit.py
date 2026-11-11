"""
Units of the plain numbers handed to the CAD kernels.

The kernels take unitless numbers, and the files that record a unit state
millimeters, so lengths are converted to millimeters and angles to degrees at
the public API and never leave this package as plain numbers.
"""

from typing import Final

from units import Angle, AngleUnit, Length, LengthUnit, MetricPrefix

from .scalar import single_finite_value

KERNEL_LENGTH_UNIT: Final[LengthUnit] = LengthUnit.M
KERNEL_LENGTH_PREFIX: Final[MetricPrefix] = MetricPrefix.MILLI


def to_kernel_length(name: str, length: Length) -> float:
    """
    Convert a single length to the kernels' length unit.

    Parameters
    ----------
    name : str
        Name of the length, used in error messages.
    length : Length
        The length.

    Returns
    -------
    float
        The length in millimeters.

    Raises
    ------
    ValueError
        If ``length`` does not hold exactly one finite value.
    """
    return single_finite_value(name, length.in_unit(KERNEL_LENGTH_UNIT, KERNEL_LENGTH_PREFIX))


def to_kernel_degrees(name: str, angle: Angle) -> float:
    """
    Convert a single angle to degrees, the kernels' angle unit.

    Parameters
    ----------
    name : str
        Name of the angle, used in error messages.
    angle : Angle
        The angle.

    Returns
    -------
    float
        The angle in degrees.

    Raises
    ------
    ValueError
        If ``angle`` does not hold exactly one finite value.
    """
    return single_finite_value(name, angle.in_unit(AngleUnit.DEGREE))
