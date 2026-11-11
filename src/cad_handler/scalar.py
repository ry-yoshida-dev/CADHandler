import math

from units import NumericArray


def single_finite_value(name: str, values: NumericArray) -> float:
    """
    Extract the one finite value of a quantity array.

    Parameters
    ----------
    name : str
        Name of the quantity, used in error messages.
    values : NumericArray
        Values of the quantity.

    Returns
    -------
    float
        The single value.

    Raises
    ------
    ValueError
        If ``values`` does not hold exactly one value or that value is not finite.
    """
    if values.size != 1:
        raise ValueError(f"{name} must hold a single value, got shape {values.shape}.")
    value = float(values.item())
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}.")
    return value
