from dataclasses import dataclass
from itertools import product
from typing import Self

import numpy as np
from cartesian_axis import Axis, CartesianCoordinateSystem
from numpy.typing import NDArray

# Reflection across the xy plane, applied first when the permutation is odd.
_XY_MIRROR: NDArray[np.float64] = np.diag([1.0, 1.0, -1.0])


@dataclass(frozen=True)
class AxisConversion:
    """
    Change of coordinate system split into operations every kernel provides.

    Converting between coordinate systems keeps each role (forward, right, and
    up) on the same values and only moves it to the target's axis for that
    role, so coordinates are permuted. An odd permutation mirrors the shape,
    so the permutation equals an optional mirror across the xy plane followed
    by quarter turns about x, then y, then z, each turning +y toward +z,
    +z toward +x, and +x toward +y respectively.

    Parameters
    ----------
    is_mirrored : bool
        Whether to mirror across the xy plane first.
    quarter_turns : tuple[int, int, int]
        Number of quarter turns, from 0 to 3, about x, y, and z.

    Raises
    ------
    ValueError
        If a quarter-turn count is outside 0 to 3.
    """

    is_mirrored: bool
    quarter_turns: tuple[int, int, int]

    def __post_init__(self) -> None:
        if any(not 0 <= turns <= 3 for turns in self.quarter_turns):
            raise ValueError(f"quarter_turns must be 0 to 3, got {self.quarter_turns}.")

    @classmethod
    def between(cls, source: CartesianCoordinateSystem, target: CartesianCoordinateSystem) -> Self:
        """
        Get the conversion from one coordinate system to another.

        Parameters
        ----------
        source : CartesianCoordinateSystem
            Coordinate system the geometry is expressed in.
        target : CartesianCoordinateSystem
            Coordinate system to express it in.

        Returns
        -------
        Self
            The mirror and quarter turns that move each role's values from
            its axis in ``source`` to its axis in ``target``.
        """
        permutation = np.zeros((3, 3), dtype=np.float64)
        for target_axis in Axis:
            role = target.axis_orientation.get_axis_name(target_axis)
            source_axis = source.axis_orientation.get_axis(role)
            permutation[target_axis.to_index, source_axis.to_index] = 1.0
        is_mirrored = bool(np.linalg.det(permutation) < 0)
        rotation = permutation @ _XY_MIRROR if is_mirrored else permutation
        for x_turns, y_turns, z_turns in product(range(4), repeat=3):
            turned = _turn(2, z_turns) @ _turn(1, y_turns) @ _turn(0, x_turns)
            if np.array_equal(turned, rotation):
                return cls(is_mirrored=is_mirrored, quarter_turns=(x_turns, y_turns, z_turns))
        raise AssertionError("Every rotation among signed permutations has quarter-turn angles.")


def _turn(axis_index: int, turns: int) -> NDArray[np.float64]:
    # Integer entries keep the comparison exact.
    first, second = [index for index in range(3) if index != axis_index]
    quarter = np.eye(3)
    quarter[[first, second], [first, second]] = 0.0
    quarter[second, first] = 1.0
    quarter[first, second] = -1.0
    if axis_index == 1:
        # About y, +z turns toward +x, the reverse of index order.
        quarter = quarter.T
    return np.linalg.matrix_power(quarter, turns)
