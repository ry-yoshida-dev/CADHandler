"""
Backend-agnostic solid modeling over PythonSCAD and CadQuery.

The backend implementations live in ``cad_handler.pythonscad`` and
``cad_handler.cadquery`` and are not imported here, so importing this package
does not load either CAD library.
"""

from .axial_length import AxialLength
from .axis_conversion import AxisConversion
from .backend import CADBackend
from .bounding_box import BoundingBox
from .displacement import Displacement
from .errors import (
    CoordinateSystemMismatchError,
    CoordinateUnitRequiredError,
    EmptySolidError,
    NonPlanarEntityError,
    OpenProfileError,
    UnknownDrawingUnitError,
    UnsupportedExportFormatError,
)
from .export_format import ExportFormat
from .modeler import Modeler
from .profile import Loop, Profile
from .solid import Solid
from .vector import Vector3

__all__ = [
    "AxialLength",
    "AxisConversion",
    "BoundingBox",
    "CADBackend",
    "CoordinateSystemMismatchError",
    "CoordinateUnitRequiredError",
    "Displacement",
    "EmptySolidError",
    "ExportFormat",
    "Loop",
    "Modeler",
    "NonPlanarEntityError",
    "OpenProfileError",
    "Profile",
    "Solid",
    "UnknownDrawingUnitError",
    "UnsupportedExportFormatError",
    "Vector3",
]
