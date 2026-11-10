# cadquery

## Overview

Backend on CadQuery, which models exact boundary representations with
OpenCASCADE. Mesh formats are tessellated at export time.

## Components

| Component | Description |
|-----------|-------------|
| [modeler.py](modeler.py) | `CadQueryModeler`: exact primitives |
| [solid.py](solid.py) | `CadQuerySolid`: wraps a CadQuery `Shape`; exports STL, 3MF, STEP, and BREP |
