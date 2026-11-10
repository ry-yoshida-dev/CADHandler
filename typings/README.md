# typings

## Overview

Type stubs for dependencies that ship without type information. mypy reads
them through `mypy_path`, and basedpyright through its default `typings`
stub path. They cover only the API `cad_handler` calls.

## Components

| Component | Description |
|-----------|-------------|
| [openscad/](openscad/__init__.pyi) | Partial stubs for the PythonSCAD C extension (`openscad` module) |
