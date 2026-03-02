CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)

CREATE TABLE classes (
            id INTEGER PRIMARY KEY,
            module_id INTEGER REFERENCES modules(id),
            name TEXT,
            is_descriptor INTEGER,
            descriptor_type TEXT, -- non_data, data
            is_nested INTEGER,
            is_contextmanager INTEGER,
            is_iterable INTEGER,
            is_iterator INTEGER,
            parent_class TEXT,
            has_metaclass INTEGER,
            metaclass TEXT);

CREATE TABLE bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER REFERENCES classes(id),
    name TEXT
)

CREATE TABLE functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER REFERENCES modules(id),
    name TEXT,
    is_async INTEGER,
    is_generator INTEGER,
    has_generator_delegation INTEGER
)

CREATE TABLE decorators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER REFERENCES classes(id),
    function_id INTEGER REFERENCES functions(id),
    name TEXT
)

CREATE TABLE (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER REFERENCES modules(id),
    name TEXT,
    type TEXT -- 'constant' | 'variable'
)

CREATE TABLE imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,,
    module_id INTEGER REFERENCES modules(id),
    source TEXT,   -- null for direct imports
    name TEXT,
    type  TEXT,-- 'direct' | 'external' | 'internal_absolute' | 'internal_relative'
    alias TEXT
)