# cad_handler

## Overview

Backend-agnostic solid modeling. `Modeler` creates primitives and extrusions,
and `Solid` combines, transforms, measures, and exports them; each backend
sub-package implements both. `dxf` turns drawings into profiles to extrude.

## Components

| Component | Description |
|-----------|-------------|
| [backend.py](backend.py) | `CADBackend`: available backends and `create_modeler()` |
| [modeler.py](modeler.py) | `Modeler`: abstract factory for boxes, cylinders, spheres, and extrusions |
| [solid.py](solid.py) | `Solid`: abstract immutable solid with boolean operations, transforms, coordinate system conversion, and export |
| [axial_length.py](axial_length.py) | `AxialLength`: length along one axis in its positive or negative direction |
| [displacement.py](displacement.py) | `Displacement`: 3D offset or position made of axial lengths |
| [bounding_box.py](bounding_box.py) | `BoundingBox`: axis-aligned extent of a solid |
| [profile.py](profile.py) | `Profile`: planar region bounded by nested closed loops |
| [export_format.py](export_format.py) | `ExportFormat`: export file formats and suffix inference |
| [vector.py](vector.py) | `Vector3`: unitless (x, y, z) tuple for scale factors, normals, and kernel numbers |
| [axis_conversion.py](axis_conversion.py) | `AxisConversion`: role-preserving axis permutation as a mirror and quarter turns |
| [kernel_unit.py](kernel_unit.py) | Conversion of lengths and angles to the plain numbers the kernels take |
| [scalar.py](scalar.py) | Extraction of a single finite value from a quantity |
| [errors/](errors/README.md) | Errors raised by solids and drawing import |
| [dxf/](dxf/README.md) | Reading profiles from DXF drawings |
| [pythonscad/](pythonscad/README.md) | PythonSCAD (OpenSCAD) backend |
| [cadquery/](cadquery/README.md) | CadQuery (OpenCASCADE) backend |
