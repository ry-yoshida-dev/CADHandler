from ..export_format import ExportFormat


class CoordinateUnitRequiredError(ValueError):
    """
    Raised when exporting to a format that records no unit without saying what its numbers mean.

    Parameters
    ----------
    export_format : ExportFormat
        The requested format.
    backend_name : str
        Name of the backend writing it.
    """

    def __init__(self, export_format: ExportFormat, backend_name: str) -> None:
        super().__init__(
            f"{backend_name} writes {export_format.name} without a unit; "
            + "give the length one coordinate stands for as coordinate_unit."
        )
        self.export_format: ExportFormat = export_format
        self.backend_name: str = backend_name
