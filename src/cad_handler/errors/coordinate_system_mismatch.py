from cartesian_axis import CartesianCoordinateSystem


class CoordinateSystemMismatchError(ValueError):
    """
    Raised when combining solids expressed in different coordinate systems.

    Convert one with ``Solid.to_coordinate_system`` first.

    Parameters
    ----------
    expected : CartesianCoordinateSystem
        Coordinate system of the receiving solid.
    actual : CartesianCoordinateSystem
        Coordinate system of the other solid.
    """

    def __init__(
        self, expected: CartesianCoordinateSystem, actual: CartesianCoordinateSystem
    ) -> None:
        super().__init__(
            f"Solids in different coordinate systems cannot be combined: {expected} and {actual}; "
            + "convert one with to_coordinate_system."
        )
        self.expected: CartesianCoordinateSystem = expected
        self.actual: CartesianCoordinateSystem = actual
