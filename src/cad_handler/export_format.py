from enum import Enum
from pathlib import Path


class ExportFormat(Enum):
    """File formats a solid can be exported to, valued by their file suffix."""

    STL = ".stl"
    THREE_MF = ".3mf"
    STEP = ".step"
    OBJ = ".obj"
    OFF = ".off"
    BREP = ".brep"

    @classmethod
    def from_path(cls, path: Path) -> "ExportFormat":
        """
        Infer the format from a file suffix, ignoring case.

        Parameters
        ----------
        path : Path
            Destination file path.

        Returns
        -------
        ExportFormat
            The format whose suffix matches ``path``. ``.stp`` is read as STEP.

        Raises
        ------
        ValueError
            If the suffix matches no format.
        """
        suffix = path.suffix.lower()
        if suffix == ".stp":
            return cls.STEP
        for export_format in cls:
            if export_format.value == suffix:
                return export_format
        supported = ", ".join(export_format.value for export_format in cls)
        raise ValueError(
            f"Unknown export suffix {path.suffix!r} in {path}; expected one of {supported}."
        )
