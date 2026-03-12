# pypkgview

Understand any Python package before you touch it.

pypkgview walks a package's source tree, statically analyzes every module via AST, and exports the full API surface into structured, queryable formats — or renders it as an interactive HTML dashboard.

No importing. No running code. Pure static analysis.

---

## Installation

```bash
pip install pypkgview
```

---

## Usage

### Export

Walk a package and export analysis data:

```bash
pypkgview export -m /path/to/package --exporter sqlite
pypkgview export -m /path/to/package --exporter json
pypkgview export -m /path/to/package --exporter yaml
```

### Dashboard

Generate a self-contained interactive HTML dashboard:

```bash
pypkgview dashboard -m /path/to/package
```

Produces `<package>_dashboard.html` — charts, rule-based insights, import composition breakdown, top modules by size. No server required. Opens directly in the browser.

---

## What it extracts

- **Classes** — bases, decorators, metaclasses, descriptors, nested classes, context managers, iterables, iterators
- **Functions** — async, generators, generator delegation, decorators
- **Imports** — direct, internal (relative/absolute), and external, with full alias resolution, classified by type
- **Constants** — module-level constants and variable declarations

---

## What it can tell you

**Architecture** — which modules are pure data, which are pure logic, where complexity is concentrated.

**Inheritance** — the full base class hierarchy across the package, who inherits what and how many times.

**API surface** — public vs internal, deprecated vs current, how much changed between versions.

**Dependencies** — what external packages a module leans on, hidden coupling to third-party internals, stdlib vs internal vs third-party import breakdown.

**Version diffing** — run against two versions of the same package and diff the databases to generate a structural changelog.

**Dashboard** — visual overview with charts, rule-based insights, and import composition. Generated from any sqlite export.

---

## Exporters

| Exporter | Output | Best for |
|---|---|---|
| `YamlExporter` | `<package>.yaml` | Human reading, diffs |
| `JSONExporter` | `<package>/<module>.json` | Programmatic consumption |
| `SqliteExporter` | `<package>.db` | Querying, analysis, dashboard |

---

## SQLite Schema

```sql
modules    (id, name)
classes    (id, module_id, name, is_descriptor, descriptor_type, is_nested,
            parent_class, has_metaclass, metaclass, is_contextmanager,
            is_iterable, is_iterator)
bases      (id, class_id, name)
functions  (id, module_id, name, is_async, is_generator, has_generator_delegation)
decorators (id, class_id, function_id, name)
constants  (id, module_id, name, type)
imports    (id, module_id, source, name, alias, type)
```

`imports.type` is one of: `direct` · `internal_absolute` · `internal_relative`

---

## Example queries

```sql
-- Most inherited base classes
SELECT name AS base, COUNT(*) AS used_by
FROM bases
GROUP BY name
ORDER BY used_by DESC;

-- Most complex modules
SELECT
    m.name AS module,
    COUNT(DISTINCT c.id) AS classes,
    COUNT(DISTINCT f.id) AS functions,
    COUNT(DISTINCT c.id) + COUNT(DISTINCT f.id) AS total_symbols
FROM modules m
LEFT JOIN classes   c ON c.module_id = m.id
LEFT JOIN functions f ON f.module_id = m.id
GROUP BY m.id
ORDER BY total_symbols DESC
LIMIT 20;

-- All generator functions
SELECT m.name AS module, f.name AS function
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE f.is_generator = 1
ORDER BY m.name;

-- Deprecated symbols
SELECT
    m.name AS module,
    COALESCE(c.name, fn.name) AS symbol,
    d.name AS decorator
FROM decorators d
JOIN modules m ON m.id = COALESCE(
    (SELECT module_id FROM classes   WHERE id = d.class_id),
    (SELECT module_id FROM functions WHERE id = d.function_id)
)
LEFT JOIN classes   c  ON c.id  = d.class_id
LEFT JOIN functions fn ON fn.id = d.function_id
WHERE LOWER(d.name) LIKE '%deprecated%';

-- Import composition — stdlib vs internal vs third-party
WITH fname AS (
    SELECT CASE WHEN source IS NULL THEN '' ELSE (source||'.') END || name AS full_name
    FROM imports
    GROUP BY full_name
)
SELECT
    CASE
        WHEN INSTR(full_name,'.') = 0 THEN full_name
        ELSE SUBSTR(full_name,1,INSTR(full_name,'.')-1)
    END AS root,
    COUNT(*) AS count
FROM fname
GROUP BY root
ORDER BY count DESC;
```

---

## Python API

```python
from pypkgview import Discover, ModuleWalker
from pypkgview import YamlExporter, JSONExporter, SqliteExporter

discover = Discover(
    file_path="/path/to/package",
    module_walker_type=ModuleWalker
)

SqliteExporter().export(discover=discover)
```

---

## Extending

To add a new exporter implement the `Exporter` protocol:

```python
from pypkgview.datastructures import Discover

class MyExporter:
    def export(self, discover: Discover) -> None:
        for module in discover:
            # module is a dict {module_name: {classes, functions, imports, constants}}
            ...
```

No changes required to any other file.

---

## Limitations

- Analyzes module-level functions only — class methods are captured on the class but not individually queryable in the current schema
- Dynamic imports (`__import__`, `importlib`) are not captured
- Type annotations are not currently extracted