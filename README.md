# CADHandler

## Overview

CADHandler (`cad_handler`) builds solids from primitives, boolean operations,
and transforms through one interface over two CAD kernels:

| Backend | Kernel | Geometry | Export formats | Formats recording their unit |
|---------|--------|----------|----------------|------------------------------|
| `CADBackend.PYTHONSCAD` | OpenSCAD via [PythonSCAD](https://pythonscad.org) | Polygon mesh; curves use `segment_count` segments | STL, 3MF, STEP, OBJ, OFF | 3MF |
| `CADBackend.CADQUERY` | OpenCASCADE via [CadQuery](https://github.com/CadQuery/cadquery) | Exact boundary representation | STL, 3MF, STEP, BREP | 3MF, STEP |

A `Modeler` creates boxes, cylinders, spheres, and extrusions of planar
`Profile`s, and every `Solid` supports `union` / `difference` / `intersection`
(also `|`, `-`, `&`), `translate`, `rotate`, `scale`, `mirror`,
`to_coordinate_system`, `bounding_box`, and `export`. Solids are immutable,
and both backends place primitives and apply transforms the same way, so code
written against `Modeler` and `Solid` gives the same shape on either one. The
wrapped library object is available as `native` for anything not covered here.

Dimensions are `Length` and `Angle` values from [Units](https://github.com/ry-yoshida-dev/Units),
so no length or angle unit is assumed. Since `Length` holds only magnitudes, a
signed offset is an `AxialLength` (a magnitude, an `Axis` from
[CartesianAxis3D](https://github.com/ry-yoshida-dev/CartesianAxis3D), and a
direction), and a `Displacement` combines one per axis.

No coordinate system is assumed either. Every `Modeler` and `Solid` carries a
`CartesianCoordinateSystem`, also from CartesianAxis3D. `to_coordinate_system`
moves the values along each role (forward, right, up) to the target's axis for
that role, and solids in different coordinate systems cannot be combined
without converting one. An extruded `Profile` is converted to the modeler's
coordinate system.

Exporting to a format that records no unit takes the length one coordinate in
the file stands for, as in `solid.export(Path("part.stl"), coordinate_unit=1.0 * MM)`.

Profiles can be read from DXF drawings, such as those exported by AutoCAD,
through [`cad_handler.dxf`](src/cad_handler/dxf/README.md): closed polylines,
circles, and chains of lines and arcs on a layer become loops, holes included,
in the unit the drawing's `$INSUNITS` header states and in AutoCAD's
coordinate system.

## Installation

```bash
uv sync
```

Both backends ship as wheels on PyPI (`pythonscad`, `cadquery`); no system
OpenSCAD install is needed.

## Usage

```python
from pathlib import Path

import numpy as np
from cartesian_axis import Axis, SoftwareCoordinateSystem
from units import Length, LengthUnit, MetricPrefix

from cad_handler import CADBackend, Displacement


MM = Length(value=np.array([1.0]), unit=LengthUnit.M, prefix=MetricPrefix.MILLI)


def offset_mm(x: float, y: float, z: float) -> Displacement:
    return Displacement.from_signed_values((x, y, z), LengthUnit.M, MetricPrefix.MILLI)


autocad = SoftwareCoordinateSystem.AUTOCAD.coordinate_system
modeler = CADBackend.CADQUERY.create_modeler(autocad)

plate = modeler.box(40.0 * MM, 20.0 * MM, 5.0 * MM)
hole = modeler.cylinder(radius=3.0 * MM, height=5.0 * MM, axis=Axis.Z)
bracket = (
    plate - hole.translate(offset_mm(10.0, 10.0, 0.0)) - hole.translate(offset_mm(30.0, 10.0, 0.0))
)

print(bracket.bounding_box.extent(Axis.X).mm)  # [40.]
bracket.export(Path("bracket.step"))
```

Using a backend's own settings and native object:

```python
from cad_handler.pythonscad import PythonSCADModeler

modeler = PythonSCADModeler(autocad, segment_count=128)
ball = modeler.sphere(10.0 * MM)
points, faces = ball.native.mesh()
```

Extruding the outline drawn on a DXF layer:

```python
from cad_handler.dxf import DXFDrawing

drawing = DXFDrawing.read(Path("plate.dxf"))
outline = drawing.profile(layer="OUTLINE", tolerance=0.01 * MM)
plate = modeler.extrude(outline, height=5.0 * MM)

unity = SoftwareCoordinateSystem.UNITY.coordinate_system
plate_for_unity = plate.to_coordinate_system(unity)
```

Importing `cad_handler` loads neither CAD library; `create_modeler()` and the
`cad_handler.pythonscad` / `cad_handler.cadquery` packages load only the one in use.

## Development

The PythonSCAD extension has no type information, so [typings/](typings/openscad/__init__.pyi)
holds partial stubs for the parts this package calls. Extend them when using
more of its API.
