# dxf

## Overview

Reads planar profiles from DXF drawings, such as those exported by AutoCAD,
with ezdxf. The drawing's `$INSUNITS` header gives the length of a drawing
unit, and a unitless drawing must be given one. Profiles lie in AutoCAD's
world coordinate system.

## Components

| Component | Description |
|-----------|-------------|
| [drawing.py](drawing.py) | `DXFDrawing`: reads a file and turns the closed loops on a layer into a `Profile` |
| [insertion_unit.py](insertion_unit.py) | `InsertionUnit`: `$INSUNITS` codes and the length each stands for |

## Examples

```python
from pathlib import Path

import numpy as np
from cartesian_axis import SoftwareCoordinateSystem
from units import Length, LengthUnit, MetricPrefix

from cad_handler import CADBackend
from cad_handler.dxf import DXFDrawing

MM = Length(value=np.array([1.0]), unit=LengthUnit.M, prefix=MetricPrefix.MILLI)

drawing = DXFDrawing.read(Path("plate.dxf"))
outline = drawing.profile(layer="OUTLINE", tolerance=0.01 * MM)
autocad = SoftwareCoordinateSystem.AUTOCAD.coordinate_system
plate = CADBackend.CADQUERY.create_modeler(autocad).extrude(outline, height=5.0 * MM)
```
