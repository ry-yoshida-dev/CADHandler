class OpenProfileError(ValueError):
    """
    Raised when the curves of a drawing layer leave chains that do not close into loops.

    Parameters
    ----------
    layer : str
        Layer the curves were read from.
    open_chain_count : int
        Number of chains whose ends do not meet.
    """

    def __init__(self, layer: str, open_chain_count: int) -> None:
        super().__init__(
            f"Layer {layer!r} has {open_chain_count} open chain(s); "
            + "every curve must belong to a closed loop."
        )
        self.layer: str = layer
        self.open_chain_count: int = open_chain_count
