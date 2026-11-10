# CADHandler

## Overview

CADHandler (`cad_handler`) builds solids from primitives, boolean operations,
and transforms through one interface over two CAD kernels:

| Backend | Kernel | Geometry | Export formats |
|---------|--------|----------|----------------|
| `CADBackend.PYTHONSCAD` | OpenSCAD via [PythonSCAD](https://pythonscad.org) | Polygon mesh; curves use `segment_count` segments | STL, 3MF, STEP, OBJ, OFF |
| `CADBackend.CADQUERY` | OpenCASCADE via [CadQuery](https://github.com/CadQuery/cadquery) | Exact boundary representation | STL, 3MF, STEP, BREP |

A `Modeler` creates boxes, cylinders, and spheres, and every `Solid` supports
`union` / `difference` / `intersection` (also `|`, `-`, `&`), `translate`,
`rotate`, `scale`, `mirror`, `bounding_box`, and `export`. Solids are immutable,
and both backends place primitives and apply transforms the same way, so code
written against `Modeler` and `Solid` gives the same shape on either one. The
wrapped library object is available as `native` for anything not covered here.

## Installation

```bash
uv sync
```

Both backends ship as wheels on PyPI (`pythonscad`, `cadquery`); no system
OpenSCAD install is needed.

## Usage

```python
from pathlib import Path

from cad_handler import CADBackend

modeler = CADBackend.CADQUERY.create_modeler()

plate = modeler.box((40.0, 20.0, 5.0))
hole = modeler.cylinder(radius=3.0, height=5.0).translate((10.0, 10.0, 0.0))
bracket = plate - hole - hole.translate((20.0, 0.0, 0.0))

print(bracket.bounding_box.size)  # (40.0, 20.0, 5.0)
bracket.export(Path("bracket.step"))
```

Using a backend's own settings and native object:

```python
from cad_handler.pythonscad import PythonSCADModeler

modeler = PythonSCADModeler(segment_count=128)
ball = modeler.sphere(radius=10.0)
points, faces = ball.native.mesh()
```

Importing `cad_handler` loads neither CAD library; `create_modeler()` and the
`cad_handler.pythonscad` / `cad_handler.cadquery` packages load only the one in use.

## Development

The PythonSCAD extension has no type information, so [typings/](typings/openscad/__init__.pyi)
holds partial stubs for the parts this package calls. Extend them when using
more of its API.
