# errors

## Overview

Errors specific to solids and drawing import. All subclass `ValueError`.

## Components

| Component | Description |
|-----------|-------------|
| [coordinate_system_mismatch.py](coordinate_system_mismatch.py) | `CoordinateSystemMismatchError`: combining solids in different coordinate systems |
| [coordinate_unit_required.py](coordinate_unit_required.py) | `CoordinateUnitRequiredError`: exporting a unitless format without `coordinate_unit` |
| [empty_solid.py](empty_solid.py) | `EmptySolidError`: the solid has no volume, e.g. after subtracting it from itself |
| [open_profile.py](open_profile.py) | `OpenProfileError`: curves on a drawing layer do not close into loops |
| [non_planar_entity.py](non_planar_entity.py) | `NonPlanarEntityError`: a drawing curve leaves the xy plane |
| [unknown_drawing_unit.py](unknown_drawing_unit.py) | `UnknownDrawingUnitError`: a drawing states no length for its units |
| [unsupported_export_format.py](unsupported_export_format.py) | `UnsupportedExportFormatError`: the backend cannot write the requested format |
