# cad_handler

## Overview

Backend-agnostic solid modeling. `Modeler` creates primitives and `Solid`
combines, transforms, measures, and exports them; each backend sub-package
implements both.

## Components

| Component | Description |
|-----------|-------------|
| [backend.py](backend.py) | `CADBackend`: available backends and `create_modeler()` |
| [modeler.py](modeler.py) | `Modeler`: abstract factory for boxes, cylinders, and spheres |
| [solid.py](solid.py) | `Solid`: abstract immutable solid with boolean operations, transforms, and export |
| [bounding_box.py](bounding_box.py) | `BoundingBox`: axis-aligned extent of a solid |
| [export_format.py](export_format.py) | `ExportFormat`: export file formats and suffix inference |
| [vector.py](vector.py) | `Vector3`: (x, y, z) tuple type |
| [errors/](errors/README.md) | Errors raised by solids |
| [pythonscad/](pythonscad/README.md) | PythonSCAD (OpenSCAD) backend |
| [cadquery/](cadquery/README.md) | CadQuery (OpenCASCADE) backend |
