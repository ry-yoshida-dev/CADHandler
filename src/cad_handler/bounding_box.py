from dataclasses import dataclass

from .vector import Vector3


@dataclass(frozen=True)
class BoundingBox:
    """
    Axis-aligned box enclosing a solid.

    Parameters
    ----------
    minimum : Vector3
        Corner with the smallest x, y, and z.
    maximum : Vector3
        Corner with the largest x, y, and z.

    Raises
    ------
    ValueError
        If any coordinate of ``minimum`` exceeds that of ``maximum``.
    """

    minimum: Vector3
    maximum: Vector3

    def __post_init__(self) -> None:
        if any(low > high for low, high in zip(self.minimum, self.maximum, strict=True)):
            raise ValueError(
                f"minimum {self.minimum} must not exceed maximum {self.maximum} on any axis."
            )

    @property
    def size(self) -> Vector3:
        """Extent along each axis."""
        x_min, y_min, z_min = self.minimum
        x_max, y_max, z_max = self.maximum
        return (x_max - x_min, y_max - y_min, z_max - z_min)

    @property
    def center(self) -> Vector3:
        """Midpoint between the two corners."""
        x_min, y_min, z_min = self.minimum
        x_max, y_max, z_max = self.maximum
        return ((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2)
