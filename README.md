# pypkgview

Comprehensive Python package analysis through static code inspection.
 
pypkgview provides complete structural analysis of Python packages without code execution. The tool extracts and catalogs classes, methods, functions, imports, decorators, and constants across entire package hierarchies. Analyze inheritance structures, identify async implementation patterns, and query complete API surfaces through multiple output formats.
 
Generates interactive HTML dashboards for visual exploration, queryable SQLite databases for advanced analysis, YAML files for version control and diffing, and JSON exports for programmatic integration.
 

---

## Installation

```bash
pip install pypkgview
```

Requirements: Python 3.8 or later. No external system dependencies.

---

## Quick Start

### Generate Interactive Dashboard

```bash
pypkgview dashboard -m /path/to/package
```

Produces a self-contained HTML file: `package_dashboard.html`. Open directly in any browser.

### Export to SQLite

```bash
pypkgview export -m /path/to/package --exporter sqlite
```

Produces `package.db`. Query with SQL.

### Export to YAML

```bash
pypkgview export -m /path/to/package --exporter yaml
```

Produces `package.yaml`. Human-readable, diffable, version-controllable.

### Export to JSON

```bash
pypkgview export -m /path/to/package --exporter json
```

Produces `package/module.json` files per module.

---

## What It Analyzes

pypkgview performs static AST analysis on every Python module. It extracts and catalogs:

### Classes

- Full inheritance hierarchy (base classes, parent class)
- Decorators applied to the class
- Class methods with full metadata (async, generator, decorated status)
- Special method detection: context manager, iterable, iterator, descriptor
- Metaclass usage
- Nested class definitions

### Methods

- Instance, class, and static methods all tracked individually
- Async methods (async def)
- Generator methods (yield, yield from)
- Generator delegation detection (yield from)
- Decorators on each method
- Standalone queryability from the database

### Functions

- Module-level functions only (class methods tracked separately)
- Async functions
- Generator functions with yield or yield from
- Generator delegation
- Applied decorators

### Imports

- Classification by type:
  - Direct: standard library and third-party packages
  - Internal absolute: from mypackage.submodule import X
  - Internal relative: from ..submodule import X
- Alias resolution (import X as Y)
- Source module tracking

### Constants and Variables

- Module-level constant assignments
- Variable tracking with reassignment detection
- Type classification

---

## The Dashboard

The dashboard is a single self-contained HTML file with no server required. Open it directly in any browser. It provides interactive visualization and exploration of your package structure with real-time filtering, sorting, and searching.

Generated with:

```bash
pypkgview dashboard -m /path/to/package
```

Produces: `package_dashboard.html`

### Top Navigation Bar

Shows high-level package statistics at a glance:

- Modules: Total count of Python modules in the package
- Classes: Total count of class definitions
- Methods: Total count of methods across all classes
- Functions: Total count of module-level functions
- Imports: Total count of import statements
- Constants: Total count of module-level constants and variables

These update in real-time based on your filters.

### Overview Panel

Starting point with aggregate statistics:

- Package name
- Total modules in the package
- Total classes
- Total methods (class-level)
- Total functions (module-level)
- Total imports
- Total constants

Gives you a quick sense of package complexity and scope.

### Modules Table

Explore package structure with sortable table showing every module:

Columns:
- Module name (fully qualified path, e.g., torch.nn.functional)
- Classes: number of classes defined in this module
- Functions: number of module-level functions
- Methods: total methods from all classes in this module
- Total: classes + functions + methods (overall complexity)

Interactions:
- Click column header to sort (click again to reverse)
- Click a module name to filter all other views to that module only
- Click again to deselect and see all modules
- Search box to filter by module name

Use for:
- Finding the most complex modules (sort by Total, descending)
- Understanding package organization
- Drilling into specific modules

### Classes Table

Complete searchable inventory of all classes with full metadata:

Columns:
- Class name
- Module it belongs to
- Bases: parent class names (multiple inheritance shown)
- Context manager: whether it has __enter__ and __exit__
- Iterable: whether it has __iter__
- Iterator: whether it has __iter__ and __next__
- Descriptor: whether it has __get__, __set__, or __delete__
- Desc. Type: "data" (has __set__) or "non_data" (read-only)
- Metaclass: whether it uses an explicit metaclass
- Methods: count of methods defined in this class

Interactions:
- Click column header to sort
- Click a class name to show only its methods in the Methods table
- Search box for class name filtering (case-insensitive)
- Sortable by any column

Use for:
- Understanding the class hierarchy (look at Bases column)
- Finding context managers (filter Context manager column)
- Finding descriptors and properties
- Identifying classes with many methods (potential refactoring candidates)
- Understanding special behaviors (iterables, context managers)

### Methods Table

All methods from all classes with full metadata. Most detailed view available.

Columns:
- Method name
- Class it belongs to
- Module path
- Async: whether the method is async def
- Generator: whether it uses yield
- Gen. Delegation: whether it uses yield from
- Decorated: whether it has any decorators
- Decorators: list of all decorators on this method

Filtering:
- Async: toggle to show "Only Async", "Only Sync", or "All"
- Generator: toggle to show "Only Generators", "No Generators", or "All"
- Decorated: toggle to show "Only Decorated", "No Decorators", or "All"
- Module: dropdown to filter by specific module
- Class: dropdown to filter by specific class
- Search box for method name

Interactions:
- Click column header to sort
- Combine multiple filters to narrow down

Use for:
- Finding all async methods (set Async = "Only Async")
- Discovering generator-based methods (set Generator = "Only Generators")
- Understanding which methods are decorated (for frameworks, properties, etc.)
- Finding deprecated methods (search "deprecat" in Decorators)
- Analyzing async coverage in the codebase

### Functions Table

All module-level functions (not methods) with full metadata:

Columns:
- Function name
- Module it belongs to
- Async: whether async def
- Generator: whether uses yield
- Gen. Delegation: whether uses yield from
- Decorated: whether has decorators
- Decorators: list of all decorators

Filtering and sorting: Same as Methods table. Focus on module-level functions only.

Use for:
- Understanding module-level API surface
- Finding utility and helper functions
- Analyzing async usage at module level

### Inheritance Graph

Interactive visualization of class inheritance relationships. Visual representation of the entire class hierarchy.

Display:
- Each class is a node (circular)
- Each inheritance relationship is a line connecting parent to child
- Colors indicate module origin (same color for classes from same module)
- Base classes positioned higher, subclasses lower
- Fully connected with all relationships visible

Interactions:
- Click and drag to pan the view
- Scroll to zoom in/out
- Click a node to highlight:
  - Direct ancestors (parents, grandparents, etc.) in darker color
  - Direct descendants (children, grandchildren, etc.) in darker color
  - Full lineage path from this class to the root in bright color
- Double-click to reset view
- Hover over a node to see full class name in tooltip

Understanding the graph:
- Deep chains (many levels of inheritance) suggest inheritance-heavy design or legacy code
- Multiple inheritance (one class with many parents) indicates mixins or plugin patterns
- Isolated branches (separate hierarchies) indicate modular, independent systems
- Wide trees (many subclasses of one parent) indicate extensible base classes

Use for:
- Understanding design patterns (composition, inheritance strategy)
- Identifying where new features might fit
- Understanding class relationships
- Spotting deep inheritance chains that might need refactoring

### Imports Panel

Breakdown of imports by type and source with charts and tables:

By Type section:
- Direct imports: count of stdlib and third-party imports
- Internal absolute: count of internal package imports (from mypackage.x)
- Internal relative: count of relative imports (from ..x)
- Pie chart showing distribution

External Packages section:
- List of top external packages imported, sorted by frequency
- Shows package name (first component of import path)
- Shows number of times imported across the codebase
- Click to expand and see which modules import it

Use for:
- Identifying external dependencies
- Spotting critical third-party packages your code relies on
- Finding over-reliance on specific libraries
- Understanding import patterns

Internal Modules section:
- List of internal modules being imported, sorted by frequency
- Shows module name (fully qualified)
- Shows number of times imported
- Click to expand and see which modules import it

Use for:
- Identifying coupling between modules
- Finding hub modules that many others depend on
- Finding isolated modules with few internal imports

### Constants Panel

Module-level constants and variables:

Columns:
- Name: constant or variable name
- Module: which module it's defined in
- Type: "constant" (never reassigned) or "variable" (reassigned)

Classification:
- Constant: assignment happens once, typically used for configuration, versions, etc.
- Variable: reassigned at least once, used for mutable module-level state

Search and sort like other tables.

Use for:
- Understanding module configuration values
- Finding module-level state
- Identifying what values are exported at module level

### Search and Filtering

Full-text search across all symbol names:

- Type in search field to filter by name (case-insensitive)
- Works on: class names, method names, function names, decorator names, module names, constant names
- Real-time results as you type
- Works across any table

Combining filters in Methods table:

1. Select Module = "torch.nn"
2. Set Async = "Only Async"
3. Set Generator = "No Generators"
4. Search for "forward"

Result: Only async methods named "forward" from torch.nn module that are not generators.

### Common Workflows

Understand a new package:
1. Open dashboard
2. Read Overview to get statistics
3. Browse Modules sorted by complexity
4. Click on major modules to see their contents
5. Use Inheritance Graph to understand design

Find async-heavy code:
1. Go to Methods table
2. Toggle Async = "Only Async"
3. Sort by Module to see which modules use async
4. Click a module to drill into async methods

Understand inheritance:
1. Go to Inheritance Graph
2. Click on a class to see its ancestors and descendants
3. Look for design patterns (deep chains, multiple inheritance, etc.)

Find deprecated APIs:
1. Go to Methods or Functions table
2. Search for "deprecat" in the Decorators column
3. Click results to see which code is deprecated

Map dependencies:
1. Go to Imports section
2. Check External Packages list
3. Click on a package to see which modules import it
4. Identify critical dependencies

Review a specific module:
1. Go to Modules
2. Click on the module name
3. See only its data in all other views
4. Check: number of classes, functions, methods, imports

Detect code smells:
- God classes: Classes table sorted by Methods (descending)
- Heavily coupled modules: Imports panel, External Packages section
- Over-decorated code: Methods table, look for methods with many decorators
- Mixed async/sync: Methods table, filter by a class, look for both async and sync methods

### Browser Compatibility

Works on:
- Chrome 90 and later
- Firefox 88 and later
- Safari 14 and later
- Edge 90 and later

Requires JavaScript enabled.

### Tips and Tricks

Sort by complexity: Go to Modules, click the Total column header twice to see least complex modules first (opposite of default).

Find public API: Go to Classes, search for items NOT starting with underscore. Same for Functions table. See what's officially exported.

Understand decorator patterns: Methods table, click Decorators column header to sort (groups decorated methods together). Look for @property, @staticmethod, @classmethod, custom framework decorators.

Identify stable vs unstable code: Async and generator methods often indicate more recent, performance-critical code. Heavily decorated code may indicate framework integration or legacy patterns.

Analyze module dependencies: Pick a module in Modules table, then go to Imports panel to see what it depends on.

Compare two packages: Generate dashboards for both, open in separate browser tabs, compare side-by-side. Which has more classes (complexity)? Which uses more async (modernization)? Which has more dependencies (coupling)?

---

## The SQLite Database

The SQLite export provides a relational schema for programmatic analysis, version diffing, and advanced queries.

### Schema Overview

Eight tables structure the data:

```
modules        - Package structure
classes        - Class definitions
methods        - Class methods
functions      - Module-level functions
bases          - Class inheritance links
decorators     - Decorator usage
constants      - Module constants and variables
imports        - All imports with classification
```

### Table Reference

#### modules

Rows: one per module in the package. Example: torch (2113 modules), fastapi (30+ modules).

Columns:
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT) - fully qualified module name, e.g., "torch.nn.functional"

#### classes

Rows: one per class definition.

Columns:
- `id` (INTEGER PRIMARY KEY)
- `module_id` (INTEGER REFERENCES modules)
- `name` (TEXT)
- `is_descriptor` (INTEGER, 0 or 1) - has __get__, __set__, or __delete__
- `descriptor_type` (TEXT or NULL) - "data" if has __set__, "non_data" if read-only
- `is_nested` (INTEGER, 0 or 1) - defined inside another class
- `is_contextmanager` (INTEGER, 0 or 1) - has __enter__ and __exit__
- `is_iterable` (INTEGER, 0 or 1) - has __iter__
- `is_iterator` (INTEGER, 0 or 1) - has __iter__ and __next__
- `parent_class` (TEXT or NULL) - immediate parent class name (for tracking direct parent)
- `has_metaclass` (INTEGER, 0 or 1) - uses explicit metaclass
- `metaclass` (TEXT or NULL) - name of the metaclass if has_metaclass is true

#### methods

Rows: one per method in every class. Not just module-level—all class methods tracked separately. Example: torch has 21,532 methods across its 4,886 classes.

Columns:
- `id` (INTEGER PRIMARY KEY)
- `class_id` (INTEGER REFERENCES classes)
- `name` (TEXT)
- `is_decorated` (INTEGER, 0 or 1) - has any decorator
- `is_async` (INTEGER, 0 or 1)
- `is_generator` (INTEGER, 0 or 1) - contains yield
- `has_generator_delegation` (INTEGER, 0 or 1) - uses yield from

#### functions

Rows: one per module-level function. Class methods are in the methods table, not here.

Columns:
- `id` (INTEGER PRIMARY KEY)
- `module_id` (INTEGER REFERENCES modules)
- `name` (TEXT)
- `is_decorated` (INTEGER, 0 or 1)
- `is_async` (INTEGER, 0 or 1)
- `is_generator` (INTEGER, 0 or 1)
- `has_generator_delegation` (INTEGER, 0 or 1)

#### bases

Rows: one per base class relationship. A class that inherits from three bases has three rows here.

Columns:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `class_id` (INTEGER REFERENCES classes) - the child class
- `name` (TEXT) - the base class name (string, not a reference)

#### decorators

Rows: one per decorator applied. A method with three decorators has three rows.

Columns:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `class_id` (INTEGER REFERENCES classes or NULL) - if decorating a class
- `function_id` (INTEGER REFERENCES functions or NULL) - if decorating a module function
- `method_id` (INTEGER REFERENCES methods or NULL) - if decorating a method
- `name` (TEXT) - decorator name (e.g., "property", "deprecated", "dataclass")

#### constants

Rows: one per module-level constant or variable.

Columns:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `module_id` (INTEGER REFERENCES modules)
- `name` (TEXT)
- `type` (TEXT) - "constant" or "variable"

#### imports

Rows: one per imported symbol. A module that imports five things has five rows.

Columns:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `module_id` (INTEGER REFERENCES modules) - the module doing the importing
- `source` (TEXT or NULL) - module being imported from. NULL for direct imports like "import json"
- `name` (TEXT) - the symbol name
- `alias` (TEXT or NULL) - alias used (for "import X as Y")
- `type` (TEXT) - one of: "direct", "internal_absolute", "internal_relative"

Import type definitions:
- `direct`: standard library or third-party (e.g., "import json", "from requests import get")
- `internal_absolute`: absolute import within package (e.g., "from mypackage.utils import helper")
- `internal_relative`: relative import within package (e.g., "from ..utils import helper")

---

## The YAML Export

The YAML format is human-readable, diffable, and suitable for version control. It organizes data hierarchically by module.

### Structure

```yaml
module.name:
  classes:
    ClassName:
      bases: [BaseClass1, BaseClass2]
      decorators: [decorator1, decorator2]
      is_contextmanager: true/false
      is_descriptor: true/false
      is_iterable: true/false
      is_iterator: true/false
      is_nested: true/false
      parent_class: null or string
      metadata:
        attrs: {}
        has_metaclass: true/false
      methods:
        method_name:
          decorators: [list]
          has_generator_delegation: true/false
          is_async: true/false
          is_decorated: true/false
          is_generator: true/false
  constants:
    constants: [CONSTANT_NAME, ...]
    variables: [VARIABLE_NAME, ...]
  functions:
    function_name:
      decorators: [list]
      has_generator_delegation: true/false
      is_async: false
      is_decorated: true/false
      is_generator: false
  imports:
    direct: [import_symbol, ...]
    external_imports:
      source.module:
        - ImportedName
        - AnotherName as Alias
    mypackage:
      absolute_imports:
        mypackage.submodule:
          - Symbol1
          - Symbol2
      relative_imports:
        [relative_path]:
          - Symbol
```

### Example

From fastapi.applications:

```yaml
fastapi.applications:
  classes:
    FastAPI:
      bases:
        - starlette.applications.Starlette
      decorators: []
      is_contextmanager: false
      is_descriptor: false
      is_iterable: false
      is_iterator: false
      is_nested: false
      parent_class: null
      metadata:
        attrs: {}
        has_metaclass: false
      methods:
        __init__:
          decorators: []
          has_generator_delegation: false
          is_async: false
          is_decorated: false
          is_generator: false
        __call__:
          decorators: []
          has_generator_delegation: false
          is_async: true
          is_decorated: false
          is_generator: false
        add_api_route:
          decorators: []
          has_generator_delegation: false
          is_async: false
          is_decorated: false
          is_generator: false
        on_event:
          decorators:
            - typing_extensions.deprecated
          has_generator_delegation: false
          is_async: false
          is_decorated: true
          is_generator: false
  constants:
    constants: []
    variables:
      - AppType
  functions: {}
  imports:
    direct: []
    external_imports:
      starlette.applications:
        - Starlette
      starlette.datastructures:
        - State
      starlette.exceptions:
        - HTTPException
      typing:
        - Annotated
        - Any
    fastapi:
      absolute_imports:
        fastapi.routing:
          - APIRouter
        fastapi.params:
          - Depends
      relative_imports: {}
```

Use YAML for version control. Diff two versions to see API changes:

```bash
pypkgview export -m mylib_v1.0 --exporter yaml
pypkgview export -m mylib_v2.0 --exporter yaml
diff mylib_v1.0.yaml mylib_v2.0.yaml
```

---

## The JSON Export

The JSON format organizes data per-module as individual JSON files within a directory. Suitable for programmatic consumption and CI/CD integration.

Structure:
```
package/
  __init__.json
  module1.json
  subpackage/
    __init__.json
    module.json
```

Each file mirrors the YAML structure for that module.

---

## Use Cases

### Understand Package Architecture

Find the most complex modules and classes:

```sql
SELECT m.name, COUNT(DISTINCT c.id) as classes,
       COUNT(DISTINCT mt.id) as methods,
       COUNT(DISTINCT mt.id) + COUNT(DISTINCT c.id) as total
FROM modules m
LEFT JOIN classes c ON c.module_id = m.id
LEFT JOIN methods mt ON c.id = mt.class_id
GROUP BY m.id
ORDER BY total DESC
LIMIT 20;
```

Identify data-only modules (pure constants, no behavior):

```sql
SELECT m.name,
       COUNT(DISTINCT c.id) as classes,
       COUNT(DISTINCT f.id) as functions,
       COUNT(DISTINCT k.id) as constants
FROM modules m
LEFT JOIN classes c ON c.module_id = m.id
LEFT JOIN functions f ON f.module_id = m.id
LEFT JOIN constants k ON k.module_id = m.id
WHERE COUNT(DISTINCT c.id) = 0 AND COUNT(DISTINCT f.id) = 0
      AND COUNT(DISTINCT k.id) > 0
GROUP BY m.id;
```

### Trace Inheritance

Find all classes inheriting from a specific base:

```sql
SELECT c.name, m.name as module FROM classes c
JOIN bases b ON b.class_id = c.id
JOIN modules m ON c.module_id = m.id
WHERE b.name = 'Exception'
ORDER BY m.name;
```

Find classes that use metaclasses:

```sql
SELECT c.name, c.metaclass, m.name as module
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.has_metaclass = 1
ORDER BY m.name;
```

### Detect Async Patterns

Find all async context managers:

```sql
SELECT c.name, m.name as module, GROUP_CONCAT(mt.name) as async_methods
FROM classes c
JOIN methods mt ON c.id = mt.class_id
JOIN modules m ON c.module_id = m.id
WHERE c.is_contextmanager = 1 AND mt.is_async = 1
GROUP BY c.id
ORDER BY m.name;
```

Find generator functions and methods:

```sql
SELECT
  'function' as type, m.name as module, f.name as name, f.is_async
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE f.is_generator = 1
UNION ALL
SELECT
  'method' as type, m.name as module, mt.name, mt.is_async
FROM methods mt
JOIN classes c ON mt.class_id = c.id
JOIN modules m ON c.module_id = m.id
WHERE mt.is_generator = 1
ORDER BY module, name;
```

Find all yield from delegations:

```sql
SELECT 'function' as type, m.name, f.name
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE f.has_generator_delegation = 1
UNION ALL
SELECT 'method', m.name, mt.name
FROM methods mt
JOIN classes c ON mt.class_id = c.id
JOIN modules m ON c.module_id = m.id
WHERE mt.has_generator_delegation = 1;
```

### Map Dependencies

Find which external packages each module depends on:

```sql
SELECT m.name as module,
       SUBSTR(i.source, 1, INSTR(i.source, '.') - 1) as external_package,
       COUNT(*) as import_count
FROM imports i
JOIN modules m ON i.module_id = m.id
WHERE i.type = 'direct' AND i.source IS NOT NULL
GROUP BY m.id, external_package
ORDER BY m.name, import_count DESC;
```

Find most-imported external packages:

```sql
SELECT SUBSTR(i.source, 1, INSTR(COALESCE(i.source, '.'), '.') - 1) as package,
       COUNT(*) as import_count
FROM imports i
WHERE i.type = 'direct'
GROUP BY package
ORDER BY import_count DESC
LIMIT 20;
```

Detect internal vs external imports ratio:

```sql
SELECT m.name as module,
       SUM(CASE WHEN i.type = 'direct' THEN 1 ELSE 0 END) as external_imports,
       SUM(CASE WHEN i.type IN ('internal_absolute', 'internal_relative') THEN 1 ELSE 0 END) as internal_imports,
       SUM(CASE WHEN i.type = 'direct' THEN 1 ELSE 0 END) * 100.0 /
       (SUM(CASE WHEN i.type IN ('internal_absolute', 'internal_relative', 'direct') THEN 1 ELSE 0 END)) as external_ratio
FROM imports i
JOIN modules m ON i.module_id = m.id
GROUP BY m.id
ORDER BY external_ratio DESC;
```

### Find Decorators

Find all deprecated symbols:

```sql
SELECT
  COALESCE(c.name, f.name, mt.name) as symbol,
  CASE WHEN c.id IS NOT NULL THEN 'class'
       WHEN f.id IS NOT NULL THEN 'function'
       ELSE 'method' END as type,
  m.name as module
FROM decorators d
JOIN modules m ON m.id = COALESCE(
  (SELECT module_id FROM classes WHERE id = d.class_id),
  (SELECT module_id FROM functions WHERE id = d.function_id),
  (SELECT c2.module_id FROM methods mt2
   JOIN classes c2 ON mt2.class_id = c2.id
   WHERE mt2.id = d.method_id)
)
LEFT JOIN classes c ON d.class_id = c.id
LEFT JOIN functions f ON d.function_id = f.id
LEFT JOIN methods mt ON d.method_id = mt.id
WHERE LOWER(d.name) LIKE '%deprecat%'
ORDER BY m.name;
```

Find all symbols with specific decorator:

```sql
SELECT
  COALESCE(c.name, f.name, mt.name) as symbol,
  CASE WHEN c.id IS NOT NULL THEN 'class'
       WHEN f.id IS NOT NULL THEN 'function'
       ELSE 'method' END as type
FROM decorators d
LEFT JOIN classes c ON d.class_id = c.id
LEFT JOIN functions f ON d.function_id = f.id
LEFT JOIN methods mt ON d.method_id = mt.id
WHERE d.name = 'property'
ORDER BY symbol;
```

### Analyze API Surface

Find public API (exported at module level):

```sql
SELECT m.name, f.name as function
FROM functions f
JOIN modules m ON f.module_id = m.id
WHERE NOT f.name LIKE '\\_%'
ORDER BY m.name;
```

Count API elements per module:

```sql
SELECT m.name,
       COUNT(DISTINCT c.id) as public_classes,
       COUNT(DISTINCT f.id) as public_functions,
       COUNT(DISTINCT mt.id) as public_methods
FROM modules m
LEFT JOIN classes c ON c.module_id = m.id AND NOT c.name LIKE '\\_%'
LEFT JOIN functions f ON f.module_id = m.id AND NOT f.name LIKE '\\_%'
LEFT JOIN methods mt ON c.id = mt.class_id AND NOT mt.name LIKE '\\_%'
WHERE c.id IS NOT NULL OR f.id IS NOT NULL OR mt.id IS NOT NULL
GROUP BY m.id
ORDER BY public_classes + public_functions DESC;
```

### Version Diffing

Compare two database exports to track API changes:

```bash
pypkgview export -m mylib_v1.0 --exporter sqlite
pypkgview export -m mylib_v2.0 --exporter sqlite
sqlite3 < diff.sql
```

Find removed classes:

```sql
SELECT v1.name FROM
  (SELECT c.name, m.name as module FROM classes c
   JOIN modules m ON c.module_id = m.id) v1
LEFT JOIN
  (SELECT c.name, m.name as module FROM mylib_v2.classes c
   JOIN mylib_v2.modules m ON c.module_id = m.id) v2
  ON v1.name = v2.name AND v1.module = v2.module
WHERE v2.name IS NULL;
```

Find new methods in existing classes:

```sql
SELECT m.name as module, c.name as class, mt.name as new_method
FROM classes c
JOIN methods mt ON c.id = mt.class_id
JOIN modules m ON c.module_id = m.id
WHERE (c.id, mt.name) NOT IN
  (SELECT c2.id, mt2.name FROM mylib_v1.classes c2
   JOIN mylib_v1.methods mt2 ON c2.id = mt2.class_id
   JOIN mylib_v1.modules m2 ON c2.module_id = m2.id
   WHERE m2.name = m.name AND c2.name = c.name)
ORDER BY m.name, c.name;
```

---

## Python API

Use pypkgview programmatically:

```python
from pypkgview import Discover, ModuleWalker
from pypkgview import SqliteExporter, JSONExporter, YamlExporter

# Analyze a package
discover = Discover(
    file_path="/path/to/package",
    module_walker_type=ModuleWalker
)

# Export to SQLite
SqliteExporter().export(discover=discover)

# Export to YAML
YamlExporter().export(discover=discover)

# Export to JSON
JSONExporter().export(discover=discover)

# Iterate modules manually
for module in discover:
    # module is a dict: {module_name: {classes, functions, imports, constants, methods}}
    print(module)
```

### Custom Exporter

Implement the Exporter protocol to create custom output formats:

```python
from pypkgview.datastructures import Discover

class CustomExporter:
    def export(self, discover: Discover) -> None:
        for module in discover:
            # module = {module_name: {classes, functions, imports, constants, methods}}
            # Process as needed
            module_name = list(module.keys())[0]
            data = module[module_name]
            # Your custom export logic
```

No other changes needed. pypkgview automatically discovers and uses it.


## Limitations

pypkgview uses static AST analysis. The following are not captured:

- Dynamic imports: `__import__()`, `importlib` module calls
- Type annotations: PEP 484 type hints, generics, TypedDict
- Docstrings: inline documentation is not parsed
- Runtime behavior: monkey-patching, dynamic class creation
- Conditional definitions: code inside try/except, if statements
- Instance attributes: class and instance variables (only module constants)
- Private modules: packages prefixed with underscore may be skipped depending on analysis settings

If your package relies heavily on dynamic metaprogramming or runtime module modification, results may be incomplete.

---

## Common Queries

### Most complex classes

```sql
SELECT c.name, m.name as module, COUNT(DISTINCT mt.id) as methods
FROM classes c
LEFT JOIN methods mt ON c.id = mt.class_id
JOIN modules m ON c.module_id = m.id
GROUP BY c.id
ORDER BY methods DESC
LIMIT 20;
```

### Inheritance chain for a specific class

```sql
WITH RECURSIVE inheritance(class_id, class_name, base_name, depth) AS (
  SELECT c.id, c.name, b.name, 1
  FROM classes c
  JOIN bases b ON b.class_id = c.id
  WHERE c.name = 'YourClassName'
  UNION ALL
  SELECT c.id, c.name, b.name, i.depth + 1
  FROM inheritance i
  JOIN classes c ON i.base_name = c.name
  JOIN bases b ON b.class_id = c.id
)
SELECT class_name, base_name, depth FROM inheritance
ORDER BY depth;
```

### All context managers

```sql
SELECT c.name, m.name as module, COUNT(DISTINCT mt.id) as methods
FROM classes c
LEFT JOIN methods mt ON c.id = mt.class_id
JOIN modules m ON c.module_id = m.id
WHERE c.is_contextmanager = 1
GROUP BY c.id
ORDER BY m.name;
```

### Async-heavy modules

```sql
SELECT m.name,
       COUNT(CASE WHEN f.is_async = 1 THEN 1 END) as async_functions,
       COUNT(CASE WHEN mt.is_async = 1 THEN 1 END) as async_methods,
       COUNT(CASE WHEN f.is_async = 1 THEN 1 END) +
       COUNT(CASE WHEN mt.is_async = 1 THEN 1 END) as total_async
FROM modules m
LEFT JOIN functions f ON f.module_id = m.id
LEFT JOIN classes c ON c.module_id = m.id
LEFT JOIN methods mt ON c.id = mt.class_id
GROUP BY m.id
HAVING total_async > 0
ORDER BY total_async DESC;
```

### Descriptors in the package

```sql
SELECT c.name, c.descriptor_type, m.name as module
FROM classes c
JOIN modules m ON c.module_id = m.id
WHERE c.is_descriptor = 1
ORDER BY m.name;
```

### Most-decorated classes

```sql
SELECT c.name, m.name as module,
       COUNT(DISTINCT d.id) as decorator_count,
       GROUP_CONCAT(DISTINCT d.name) as decorators
FROM classes c
LEFT JOIN decorators d ON d.class_id = c.id
JOIN modules m ON c.module_id = m.id
GROUP BY c.id
HAVING decorator_count > 0
ORDER BY decorator_count DESC;
```

### Modules with no dependencies

```sql
SELECT m.name FROM modules m
WHERE m.id NOT IN (SELECT DISTINCT module_id FROM imports)
ORDER BY m.name;
```

### High-coupling modules

```sql
SELECT m.name,
       COUNT(DISTINCT i.source) as external_deps,
       COUNT(DISTINCT CASE WHEN i.type IN ('internal_absolute', 'internal_relative') THEN i.source END) as internal_deps
FROM modules m
LEFT JOIN imports i ON i.module_id = m.id
GROUP BY m.id
ORDER BY external_deps + internal_deps DESC
LIMIT 20;
```

---

## Example Analysis

Analyzing FastAPI (30 modules, 40+ classes):

```bash
pypkgview export -m fastapi --exporter sqlite
```

Questions you can answer:

1. What is FastAPI's main entry point?
   - Query: Find the FastAPI class and its methods

2. What external packages does FastAPI depend on?
   - Query: Group imports by source

3. Which FastAPI classes use async?
   - Query: Find classes with async methods

4. What decorators does FastAPI use internally?
   - Query: Find all decorators and what they decorate

5. How is the routing system structured?
   - Query: Find classes with "route" in the name, their inheritance, methods

6. Are there deprecated APIs?
   - Query: Find symbols with @deprecated decorator

All answerable from a single command with no code execution.

---

## Troubleshooting

### Dashboard is blank

Ensure the package path is correct and readable. The dashboard requires at least one module to display.

### SQLite file is very large

For large packages, the database can be 50MB+. This is normal. Ensure you have sufficient disk space.

### Imports show as "direct" but I expected internal

Imports are classified as "direct" if they are not prefixed with the package name. Check that imports are using relative paths (from ..x) or absolute package paths (from mypackage.x) for internal detection.

### Some classes or methods are missing

Dynamic class creation and runtime modifications are not captured by static analysis. Only definitions in source files are analyzed.

---

## Contributing

Contributions welcome. File issues or submit pull requests.

---

## License

MIT

---

## See Also

- SQLite: sqlite.org
- Python AST: docs.python.org/library/ast
- YAML specification: yaml.org