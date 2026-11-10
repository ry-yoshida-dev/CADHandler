class EmptySolidError(ValueError):
    """Raised when an operation needs volume but the solid has none, e.g. after a full difference."""
