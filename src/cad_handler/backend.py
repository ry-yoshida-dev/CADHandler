from enum import Enum

from .modeler import Modeler
from .solid import Solid


class CADBackend(Enum):
    """CAD kernels this package can model with."""

    PYTHONSCAD = "pythonscad"
    """OpenSCAD's CGAL/Manifold mesh kernel through PythonSCAD; fast, approximates curves with segments."""

    CADQUERY = "cadquery"
    """OpenCASCADE's exact boundary representation through CadQuery; suited to STEP exchange."""

    def create_modeler(self) -> Modeler[Solid]:
        """
        Create a modeler for this backend with default settings.

        Only the selected backend's library is imported, so the other one does
        not need to load.

        Returns
        -------
        Modeler[Solid]
            A modeler whose primitives belong to this backend.
        """
        match self:
            case CADBackend.PYTHONSCAD:
                from .pythonscad import PythonSCADModeler

                return PythonSCADModeler()
            case CADBackend.CADQUERY:
                from .cadquery import CadQueryModeler

                return CadQueryModeler()
