from dataclasses import dataclass

import numpy as np
from cartesian_axis import CartesianCoordinateSystem
from numpy.typing import NDArray
from units import Length, LengthUnit, MetricPrefix

from .scalar import single_finite_value

type Loop = NDArray[np.float64]
"""Vertices of a closed loop as an (n, 2) array of x and y, without repeating the first one."""


@dataclass(frozen=True, eq=False)
class Profile:
    """
    Planar region in the xy plane of a coordinate system, bounded by closed loops.

    Loops nest by the even-odd rule: the region is inside an odd number of
    loops, so a loop within one other loop is a hole and a loop within a hole
    is an island.

    Parameters
    ----------
    loops : tuple[Loop, ...]
        Closed loops, each an (n, 2) array of at least three vertices.
    coordinate_unit : Length
        Length that one coordinate step stands for, as a single value; for
        example 1 mm when the coordinates are millimeters.
    coordinate_system : CartesianCoordinateSystem
        Coordinate system whose xy plane holds the loops.

    Raises
    ------
    ValueError
        If there is no loop, a loop is not an (n, 2) array of at least three
        finite vertices, or ``coordinate_unit`` is not a single finite,
        positive value.
    """

    loops: tuple[Loop, ...]
    coordinate_unit: Length
    coordinate_system: CartesianCoordinateSystem

    def __post_init__(self) -> None:
        if not self.loops:
            raise ValueError("A profile needs at least one loop.")
        for index, loop in enumerate(self.loops):
            if loop.ndim != 2 or loop.shape[1] != 2 or loop.shape[0] < 3:
                raise ValueError(
                    f"Loop {index} must have shape (n, 2) with n >= 3, got {loop.shape}."
                )
            if not np.all(np.isfinite(loop)):
                raise ValueError(f"Loop {index} must have finite coordinates.")
        if single_finite_value("coordinate_unit", self.coordinate_unit.value) <= 0:
            raise ValueError(f"coordinate_unit must be positive, got {self.coordinate_unit}.")

    def loops_in(
        self, unit: LengthUnit, prefix: MetricPrefix = MetricPrefix.NONE
    ) -> tuple[Loop, ...]:
        """
        Express the loops in a unit.

        Parameters
        ----------
        unit : LengthUnit
            Unit to express the coordinates in.
        prefix : MetricPrefix
            Prefix of ``unit``, or ``MetricPrefix.NONE`` for the unit itself.

        Returns
        -------
        tuple[Loop, ...]
            New arrays of the loop coordinates in that unit.

        Raises
        ------
        ValueError
            If ``unit`` takes no prefix but one is given.
        """
        scale = float(self.coordinate_unit.in_unit(unit, prefix).item())
        return tuple(loop * scale for loop in self.loops)

    @property
    def nesting_depths(self) -> tuple[int, ...]:
        """
        Number of other loops enclosing each loop.

        Even depths add area and odd depths cut holes. Each loop is tested by
        its first vertex, so loops are expected not to cross one another.
        """
        return tuple(
            sum(
                _encloses(other, loop[0])
                for other_index, other in enumerate(self.loops)
                if other_index != index
            )
            for index, loop in enumerate(self.loops)
        )


def _encloses(loop: Loop, point: NDArray[np.float64]) -> bool:
    # Even-odd ray casting toward +x, vectorized over the loop's edges.
    x, y = float(point[0]), float(point[1])
    starts = loop
    ends = np.roll(loop, -1, axis=0)
    is_straddling = (starts[:, 1] > y) != (ends[:, 1] > y)
    rise = np.where(is_straddling, ends[:, 1] - starts[:, 1], 1.0)
    crossing_x = starts[:, 0] + (y - starts[:, 1]) * (ends[:, 0] - starts[:, 0]) / rise
    return bool(np.count_nonzero(is_straddling & (x < crossing_x)) % 2)
