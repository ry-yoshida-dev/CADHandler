from ..export_format import ExportFormat


class UnsupportedExportFormatError(ValueError):
    """
    Raised when a backend cannot write the requested export format.

    Parameters
    ----------
    export_format : ExportFormat
        The requested format.
    backend_name : str
        Name of the backend that rejected it.
    supported_formats : frozenset[ExportFormat]
        Formats the backend can write.
    """

    def __init__(
        self,
        export_format: ExportFormat,
        backend_name: str,
        supported_formats: frozenset[ExportFormat],
    ) -> None:
        supported = ", ".join(sorted(supported.name for supported in supported_formats))
        super().__init__(
            f"{backend_name} cannot export {export_format.name}; supported formats: {supported}."
        )
        self.export_format: ExportFormat = export_format
        self.backend_name: str = backend_name
        self.supported_formats: frozenset[ExportFormat] = supported_formats
