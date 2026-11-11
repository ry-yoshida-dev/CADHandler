class NonPlanarEntityError(ValueError):
    """
    Raised when a drawing curve does not lie in the xy plane.

    Parameters
    ----------
    layer : str
        Layer the curve was read from.
    entity_type : str
        Drawing entity type of the curve, such as ``LINE``.
    """

    def __init__(self, layer: str, entity_type: str) -> None:
        super().__init__(
            f"A {entity_type} on layer {layer!r} leaves the xy plane; "
            + "only planar profiles at zero elevation can be read."
        )
        self.layer: str = layer
        self.entity_type: str = entity_type
