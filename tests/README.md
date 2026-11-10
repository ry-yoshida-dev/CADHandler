# tests

## Overview

Pytest suite. The `modeler` fixture runs each contract test against both
backends, so they are checked to produce the same geometry.

## Components

| Component | Description |
|-----------|-------------|
| [conftest.py](conftest.py) | Backend parametrization and bounding-box assertion helper |
| [test_modeler.py](test_modeler.py) | Primitive placement and input validation |
| [test_solid.py](test_solid.py) | Boolean operations, transforms, immutability, and backend mixing |
| [test_export.py](test_export.py) | Writing each supported format and rejecting the rest |
| [test_value_types.py](test_value_types.py) | `ExportFormat`, `BoundingBox`, and `CADBackend` |
