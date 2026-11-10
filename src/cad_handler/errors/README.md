# errors

## Overview

Errors specific to solids. Both subclass `ValueError`.

## Components

| Component | Description |
|-----------|-------------|
| [empty_solid.py](empty_solid.py) | `EmptySolidError`: the solid has no volume, e.g. after subtracting it from itself |
| [unsupported_export_format.py](unsupported_export_format.py) | `UnsupportedExportFormatError`: the backend cannot write the requested format |
