# pythonscad

## Overview

Backend on PythonSCAD, OpenSCAD's Python interface. Solids are polygon meshes,
and `segment_count` sets how finely cylinders and spheres are approximated.

## Components

| Component | Description |
|-----------|-------------|
| [modeler.py](modeler.py) | `PythonSCADModeler`: primitives with a configurable `segment_count` |
| [solid.py](solid.py) | `PythonSCADSolid`: wraps a PythonSCAD object; exports STL, 3MF, STEP, OBJ, and OFF |
