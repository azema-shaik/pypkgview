# pypkgview

A Python package introspection tool that parses source code via AST and exports the full API surface into structured, queryable formats.

## What it does

pypkgview walks a Python package's source tree, statically analyzes every module, and extracts:

- **Classes** — bases, decorators, metaclasses, descriptors, nested classes
- **Functions** — async, generators, generator delegation, decorators
- **Imports** — direct, internal (relative/absolute), and external, with full alias resolution
- **Constants** — module-level constants and variable declarations

No importing. No running code. Pure AST analysis.

## Why it's useful

Most tools that understand Python packages require importing them. pypkgview works entirely from source — meaning it works on packages you don't have installed, packages with heavy dependencies, or packages you're auditing without wanting to execute.

The structured output is queryable. With the SQLite exporter you can ask questions like:

```sql
-- What is the most inherited base class across the package?
SELECT b.name, COUNT(*) as count
FROM bases b
GROUP BY b.name
ORDER BY count DESC;

-- Which modules have the most complex API surface?
SELECT m.name, COUNT(DISTINCT c.id) as classes, COUNT(DISTINCT f.id) as functions
FROM modules m
LEFT JOIN classes c ON c.module_id = m.id
LEFT JOIN functions f ON f.module_id = m.id
GROUP BY m.id
ORDER BY classes + functions DESC;

-- Find all generator functions
SELECT m.name, f.name, f.has_generator_delegation
FROM functions f
JOIN modules m ON m.id = f.module_id
WHERE f.is_generator = 1;
```

## Installation

```bash
pip install pypkgview
```

## Usage

```python
from pypkgview.engine import DiscoverEngine
from pypkgview.walker import ModuleWalker
from pypkgview.exporters import YamlExporter, JSONExporter, SqliteExporter

# point at the package source directory
engine = DiscoverEngine(
    file_path="/path/to/package",
    module_walker_type=ModuleWalker
)

# export to YAML
YamlExporter().export(engine)

# export to JSON
JSONExporter().export(engine)

# export to SQLite
SqliteExporter().export(engine)
```

## Exporters

| Exporter | Output | Best for |
|---|---|---|
| `YamlExporter` | `<package>.yaml` | Human reading, diffs |
| `JSONExporter` | `<package>/<module>.json` | Programmatic consumption |
| `SqliteExporter` | `<package>.db` | Querying, analysis |

## Schema

The SQLite exporter produces the following schema:

```sql
modules    (id, name)
classes    (id, module_id, name, is_descriptor, descriptor_type, is_nested, parent_class, has_metaclass, metaclass)
bases      (id, class_id, name)
functions  (id, module_id, name, is_async, is_generator, has_generator_delegation)
decorators (id, class_id, function_id, name)
constants  (id, module_id, name, type)
imports    (id, module_id, source, name, type)
```

## What it can tell you

**Architecture** — which modules are pure data, which are pure logic, where complexity is concentrated.

**Inheritance** — the full base class hierarchy across the package, who inherits what and how many times.

**API surface** — public vs internal, deprecated vs current, how much changed between versions.

**Dependencies** — what external packages a module leans on, hidden coupling to third-party internals.

**Version diffing** — run against two versions of the same package and diff the databases to generate a structural changelog.

## Example findings

Running pypkgview against real packages reveals things that docs won't tell you:

- **FastAPI** — the entire OpenAPI schema lives in one module (`fastapi.openapi.models`, 42 classes). Zero async module-level functions — all async logic lives inside class methods.
- **Pydantic v2** — ships a full copy of v1 internally (`pydantic.v1.*`). The two codebases are nearly identical in size. The real engine lives in `pydantic._internal` — 28 modules, 190 functions, mostly invisible to users.

## Architecture

```
datastructures.py   — typed data containers (Class, Discover Protocol)
parser.py           — AST NodeVisitor, extracts raw nodes
walker.py           — resolves AST nodes into structured dicts, handles import aliasing
engine.py           — walks the file system, orchestrates walker per module
exporters.py        — pluggable export backends (YAML, JSON, SQLite)
```

Exporters are interchangeable via the `Exporter` Protocol — adding a new export format requires no changes to any other file.

## Extending

To add a new exporter implement the `Exporter` Protocol:

```python
from pypkgview.datastructures import Discover
from pypkgview.exporters import Exporter

class MyExporter:
    def export(self, discover: Discover) -> None:
        for module in discover:
            # module is a dict {module_name: {classes, functions, imports, constants}}
            ...
```

## Limitations

- Analyzes module-level functions only — class methods are captured on the class but not individually queryable in the current schema
- Import resolution depends on static analysis — dynamic imports (`__import__`, `importlib`) are not captured
- Type annotations are not currently extracted
