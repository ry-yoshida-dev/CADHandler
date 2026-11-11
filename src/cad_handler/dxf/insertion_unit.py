import math
from enum import Enum

import numpy as np
from units import Length, LengthUnit, MetricPrefix

from ..errors import UnknownDrawingUnitError


class InsertionUnit(Enum):
    """Drawing units a DXF file states in its ``$INSUNITS`` header, valued by their code."""

    UNITLESS = 0
    INCH = 1
    FOOT = 2
    MILE = 3
    MILLIMETER = 4
    CENTIMETER = 5
    METER = 6
    KILOMETER = 7
    MICROINCH = 8
    MIL = 9
    YARD = 10
    ANGSTROM = 11
    NANOMETER = 12
    MICROMETER = 13
    DECIMETER = 14
    DECAMETER = 15
    HECTOMETER = 16
    GIGAMETER = 17
    ASTRONOMICAL_UNIT = 18
    LIGHT_YEAR = 19
    PARSEC = 20
    US_SURVEY_FOOT = 21

    @classmethod
    def from_code(cls, code: int) -> "InsertionUnit":
        """
        Look up a unit by its ``$INSUNITS`` code.

        Parameters
        ----------
        code : int
            The header value.

        Returns
        -------
        InsertionUnit
            The unit with that code.

        Raises
        ------
        UnknownDrawingUnitError
            If no unit has that code.
        """
        for unit in cls:
            if unit.value == code:
                return unit
        raise UnknownDrawingUnitError(f"$INSUNITS code {code} names no known unit.")

    @property
    def length(self) -> Length:
        """
        Length one drawing unit stands for.

        Raises
        ------
        UnknownDrawingUnitError
            If the drawing is unitless.
        """
        match self:
            case InsertionUnit.UNITLESS:
                raise UnknownDrawingUnitError(
                    "The drawing is unitless; give the length one drawing unit stands for."
                )
            case InsertionUnit.INCH:
                return _length(1.0, LengthUnit.INCH)
            case InsertionUnit.FOOT:
                return _length(1.0, LengthUnit.FOOT)
            case InsertionUnit.MILE:
                return _length(1.0, LengthUnit.MILE)
            case InsertionUnit.MILLIMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.MILLI)
            case InsertionUnit.CENTIMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.CENTI)
            case InsertionUnit.METER:
                return _length(1.0, LengthUnit.M)
            case InsertionUnit.KILOMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.KILO)
            case InsertionUnit.MICROINCH:
                return _length(1e-6, LengthUnit.INCH)
            case InsertionUnit.MIL:
                return _length(1e-3, LengthUnit.INCH)
            case InsertionUnit.YARD:
                return _length(1.0, LengthUnit.YARD)
            case InsertionUnit.ANGSTROM:
                return _length(0.1, LengthUnit.M, MetricPrefix.NANO)
            case InsertionUnit.NANOMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.NANO)
            case InsertionUnit.MICROMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.MICRO)
            case InsertionUnit.DECIMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.DECI)
            case InsertionUnit.DECAMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.DECA)
            case InsertionUnit.HECTOMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.HECTO)
            case InsertionUnit.GIGAMETER:
                return _length(1.0, LengthUnit.M, MetricPrefix.GIGA)
            case InsertionUnit.ASTRONOMICAL_UNIT:
                return _length(_ASTRONOMICAL_UNIT_METERS, LengthUnit.M)
            case InsertionUnit.LIGHT_YEAR:
                return _length(9_460_730_472_580_800.0, LengthUnit.M)
            case InsertionUnit.PARSEC:
                return _length(_ASTRONOMICAL_UNIT_METERS * 648_000 / math.pi, LengthUnit.M)
            case InsertionUnit.US_SURVEY_FOOT:
                return _length(1200 / 3937, LengthUnit.M)


_ASTRONOMICAL_UNIT_METERS: float = 149_597_870_700.0


def _length(value: float, unit: LengthUnit, prefix: MetricPrefix = MetricPrefix.NONE) -> Length:
    return Length(value=np.array([value]), unit=unit, prefix=prefix)
