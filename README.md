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

# pypkgview — SQL Insight Queries

A collection of queries to extract meaningful structural insights from any `.sqlite` file produced by `pypkgview`.

---

## 📦 Package Overview

**High-level snapshot of the whole package**
```sql
SELECT
    (SELECT COUNT(*) FROM modules)   AS modules,
    (SELECT COUNT(*) FROM classes)   AS classes,
    (SELECT COUNT(*) FROM functions) AS functions,
    (SELECT COUNT(*) FROM imports)   AS imports,
    (SELECT COUNT(*) FROM constants) AS constants,
    (SELECT COUNT(*) FROM decorators) AS decorators;
```

---

## 🏗️ Module Complexity

**Which modules are the most complex (by combined class + function count)?**
```sql
SELECT
    m.name AS module,
    COUNT(DISTINCT c.id) AS classes,
    COUNT(DISTINCT f.id) AS functions,
    COUNT(DISTINCT c.id) + COUNT(DISTINCT f.id) AS total_symbols
FROM modules m
LEFT JOIN classes  c ON c.module_id = m.id
LEFT JOIN functions f ON f.module_id = m.id
GROUP BY m.id
ORDER BY total_symbols DESC
LIMIT 20;
```

**Modules with no classes and no functions (possibly pure re-export or config modules)**
```sql
SELECT m.name
FROM modules m
LEFT JOIN classes   c ON c.module_id = m.id
LEFT JOIN functions f ON f.module_id = m.id
WHERE c.id IS NULL AND f.id IS NULL
ORDER BY m.name;
```

---

## 🔗 Inheritance

**Most commonly inherited base classes (what is the package built on top of?)**
```sql
SELECT name AS base, COUNT(*) AS used_by
FROM bases
GROUP BY name
ORDER BY used_by DESC
LIMIT 20;
```

**Deepest inheritance chains — classes with the most bases**
```sql
SELECT c.name AS class, m.name AS module, COUNT(b.id) AS base_count
FROM classes c
JOIN modules m ON c.module_id = m.id
JOIN bases b ON b.class_id = c.id
GROUP BY c.id
ORDER BY base_count DESC
LIMIT 15;
```

**Classes with multiple inheritance (more than one base)**
```sql
SELECT c.name AS class, m.name AS module, COUNT(b.id) AS num_bases
FROM classes c
JOIN modules m ON c.module_id = m.id
JOIN bases b ON b.class_id = c.id
GROUP BY c.id
HAVING num_bases > 1
ORDER BY num_bases DESC;
```

**Which external libraries does the inheritance tree depend on?**
```sql
SELECT
    CASE
        WHEN name LIKE 'builtins.%'       THEN 'builtins'
        WHEN name LIKE 'typing.%'         THEN 'typing'
        WHEN name LIKE 'typing_extensions.%' THEN 'typing_extensions'
        WHEN name LIKE 'enum.%'           THEN 'enum'
        WHEN name LIKE 'abc.%'            THEN 'abc'
        ELSE SUBSTR(name, 1, INSTR(name, '.') - 1)
    END AS origin,
    COUNT(*) AS count
FROM bases
WHERE name NOT LIKE (SELECT name FROM modules LIMIT 1) || '%'
GROUP BY origin
ORDER BY count DESC
LIMIT 15;
```

---

## 🎨 Decorators

**Most used decorators across the whole package**
```sql
SELECT name AS decorator, COUNT(*) AS uses
FROM decorators
GROUP BY name
ORDER BY uses DESC
LIMIT 20;
```

**Decorators used only on classes**
```sql
SELECT name, COUNT(*) AS uses
FROM decorators
WHERE class_id IS NOT NULL AND function_id IS NULL
GROUP BY name
ORDER BY uses DESC;
```

**Decorators used only on functions**
```sql
SELECT name, COUNT(*) AS uses
FROM decorators
WHERE function_id IS NOT NULL AND class_id IS NULL
GROUP BY name
ORDER BY uses DESC;
```

**Most decorated modules (decoration density)**
```sql
SELECT m.name AS module, COUNT(d.id) AS decorator_count
FROM modules m
JOIN classes  c ON c.module_id = m.id
JOIN decorators d ON d.class_id = c.id
GROUP BY m.id
UNION ALL
SELECT m.name, COUNT(d.id)
FROM modules m
JOIN functions f ON f.module_id = m.id
JOIN decorators d ON d.function_id = f.id
GROUP BY m.id
ORDER BY decorator_count DESC
LIMIT 15;
```

---

## ⚙️ Functions

**Async vs sync function breakdown by module**
```sql
SELECT
    m.name AS module,
    COUNT(f.id) AS total,
    SUM(f.is_async) AS async_count,
    ROUND(100.0 * SUM(f.is_async) / COUNT(f.id), 1) AS async_pct
FROM modules m
JOIN functions f ON f.module_id = m.id
GROUP BY m.id
HAVING async_count > 0
ORDER BY async_pct DESC;
```

**All generator functions (lazy / streaming APIs)**
```sql
SELECT m.name AS module, f.name AS function, f.has_generator_delegation
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE f.is_generator = 1
ORDER BY m.name, f.name;
```

**Functions that use `yield from` (generator delegation — composable generators)**
```sql
SELECT m.name AS module, f.name AS function
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE f.has_generator_delegation = 1
ORDER BY m.name;
```

---

## 🧬 Class Traits

**All descriptor classes with their type**
```sql
SELECT m.name AS module, c.name AS class, c.descriptor_type
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.is_descriptor = 1
ORDER BY c.descriptor_type, m.name;
```

**All context manager classes**
```sql
SELECT m.name AS module, c.name AS class
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.is_contextmanager = 1
ORDER BY m.name;
```

**Iterable vs iterator classes**
```sql
SELECT
    m.name AS module,
    c.name AS class,
    CASE
        WHEN c.is_iterator = 1 THEN 'iterator'
        ELSE 'iterable'
    END AS type
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.is_iterable = 1 OR c.is_iterator = 1
ORDER BY type, m.name;
```

**Classes using metaclasses (advanced metaprogramming)**
```sql
SELECT m.name AS module, c.name AS class, c.metaclass
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.has_metaclass = 1
ORDER BY c.metaclass, m.name;
```

**Nested classes and their parents**
```sql
SELECT m.name AS module, c.name AS class, c.parent_class
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.is_nested = 1
ORDER BY m.name;
```

---

## 📥 Imports & Dependencies

**What does this package import most from itself? (internal coupling)**
```sql
SELECT source, COUNT(*) AS import_count
FROM imports
WHERE type IN ('internal_absolute', 'internal_relative')
GROUP BY source
ORDER BY import_count DESC
LIMIT 20;
```

**Most imported internal symbols (what is the core API?)**
```sql
SELECT name, COUNT(*) AS times_imported
FROM imports
WHERE type IN ('internal_absolute', 'internal_relative')
GROUP BY name
ORDER BY times_imported DESC
LIMIT 20;
```

**Modules that rely most heavily on internal imports (tightly coupled)**
```sql
SELECT
    m.name AS module,
    COUNT(i.id) AS internal_imports,
    ROUND(100.0 * COUNT(i.id) /
        (SELECT COUNT(*) FROM imports i2 WHERE i2.module_id = m.id), 1
    ) AS internal_pct
FROM modules m
JOIN imports i ON i.module_id = m.id
WHERE i.type IN ('internal_absolute', 'internal_relative')
GROUP BY m.id
ORDER BY internal_imports DESC
LIMIT 20;
```

**Direct (third-party / stdlib) dependencies used across the package**
```sql
SELECT name, COUNT(*) AS used_in_n_modules
FROM imports
WHERE type = 'direct'
GROUP BY name
ORDER BY used_in_n_modules DESC
LIMIT 20;
```

**Imports that use aliases (can indicate naming conflicts or long names)**
```sql
SELECT source, name, alias, m.name AS module
FROM imports i
JOIN modules m ON i.module_id = m.id
WHERE alias IS NOT NULL
ORDER BY alias;
```

---

## 🗂️ Constants & Variables

**Module-level constants vs variables breakdown**
```sql
SELECT type, COUNT(*) AS count
FROM constants
GROUP BY type;
```

**Modules with the most module-level constants**
```sql
SELECT m.name AS module, COUNT(cn.id) AS constant_count
FROM modules m
JOIN constants cn ON cn.module_id = m.id
WHERE cn.type = 'constant'
GROUP BY m.id
ORDER BY constant_count DESC
LIMIT 15;
```

---

## 🔍 Interesting Combinations

**God classes — large, complex, with many traits**
```sql
SELECT
    m.name AS module,
    c.name AS class,
    (SELECT COUNT(*) FROM bases b WHERE b.class_id = c.id) AS num_bases,
    (SELECT COUNT(*) FROM decorators d WHERE d.class_id = c.id) AS num_decorators,
    c.is_descriptor,
    c.is_contextmanager,
    c.is_iterable,
    c.has_metaclass
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE
    (SELECT COUNT(*) FROM bases b WHERE b.class_id = c.id) > 2
    OR c.has_metaclass = 1
    OR (c.is_descriptor = 1 AND c.is_contextmanager = 1)
ORDER BY num_bases DESC;
```

**Modules that are purely functional (no classes at all)**
```sql
SELECT m.name AS module, COUNT(f.id) AS function_count
FROM modules m
LEFT JOIN classes  c ON c.module_id = m.id
JOIN      functions f ON f.module_id = m.id
WHERE c.id IS NULL
GROUP BY m.id
ORDER BY function_count DESC;
```

**Deprecated symbols (decorated with anything containing 'deprecated')**
```sql
SELECT
    m.name AS module,
    COALESCE(c.name, fn.name) AS symbol,
    CASE WHEN d.class_id IS NOT NULL THEN 'class' ELSE 'function' END AS kind,
    d.name AS decorator
FROM decorators d
JOIN modules m ON m.id = COALESCE(
    (SELECT module_id FROM classes  WHERE id = d.class_id),
    (SELECT module_id FROM functions WHERE id = d.function_id)
)
LEFT JOIN classes   c  ON c.id  = d.class_id
LEFT JOIN functions fn ON fn.id = d.function_id
WHERE LOWER(d.name) LIKE '%deprecated%'
ORDER BY m.name;
```

**Circular-risk modules — modules that import from many other internal modules**
```sql
SELECT m.name AS module, COUNT(DISTINCT i.source) AS imports_from_n_modules
FROM modules m
JOIN imports i ON i.module_id = m.id
WHERE i.type IN ('internal_absolute', 'internal_relative')
GROUP BY m.id
ORDER BY imports_from_n_modules DESC
LIMIT 15;
```

## Limitations

- Analyzes module-level functions only — class methods are captured on the class but not individually queryable in the current schema
- Import resolution depends on static analysis — dynamic imports (`__import__`, `importlib`) are not captured
- Type annotations are not currently extracted
