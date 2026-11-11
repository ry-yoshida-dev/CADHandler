# tests

## Overview

Pytest suite. The `modeler` fixture runs each contract test against both
backends, so they are checked to produce the same geometry.

## Components

| Component | Description |
|-----------|-------------|
| [conftest.py](conftest.py) | Backend parametrization, AutoCAD coordinate system, unit constants, and bounding-box assertion |
| [test_modeler.py](test_modeler.py) | Primitive placement, extrusion, and input validation |
| [test_solid.py](test_solid.py) | Boolean operations, transforms, immutability, and backend mixing |
| [test_export.py](test_export.py) | Writing each supported format, coordinate units of unitless formats, and rejecting the rest |
| [test_value_types.py](test_value_types.py) | `ExportFormat`, `BoundingBox`, and `CADBackend` |
| [test_axial_length.py](test_axial_length.py) | Direction, unit conversion, and equality of `AxialLength` |
| [test_displacement.py](test_displacement.py) | Components and arithmetic of `Displacement` |
| [test_coordinate_system.py](test_coordinate_system.py) | Converting solids and extrusions between coordinate systems |
| [test_profile.py](test_profile.py) | Validation, unit conversion, and nesting of `Profile` |
| [test_dxf.py](test_dxf.py) | Reading DXF units, loops, and holes, and rejecting open or non-planar curves |
