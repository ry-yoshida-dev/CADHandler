"""
Backend-agnostic solid modeling over PythonSCAD and CadQuery.

The backend implementations live in ``cad_handler.pythonscad`` and
``cad_handler.cadquery`` and are not imported here, so importing this package
does not load either CAD library.
"""

from .backend import CADBackend
from .bounding_box import BoundingBox
from .errors import EmptySolidError, UnsupportedExportFormatError
from .export_format import ExportFormat
from .modeler import Modeler
from .solid import Solid
from .vector import Vector3

__all__ = [
    "BoundingBox",
    "CADBackend",
    "EmptySolidError",
    "ExportFormat",
    "Modeler",
    "Solid",
    "UnsupportedExportFormatError",
    "Vector3",
]
