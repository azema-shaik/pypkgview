import os 
import logging
from typing import Protocol
from .datastructures import Discover as EngineProtocol


logger = logging.getLogger(__name__)

class StreamExporter:
    
    def  export(self, discover: EngineProtocol): 
        logger.info(f'StreamExporter chosen.')

        import pprint
        print(f"Package: \033[1;38;5;9m{discover.package}\033[0m")
        for dct in discover:
            module_name = list(dct)[0]
            print(f"Parsing: \033[1;38;5;10m{discover.package}\033[0m")
            pprint.pprint(dct)




class YamlExporter:
    def  export(self, discover: EngineProtocol): 
        
        logger.info(f'YamlExporter chosen.')
        try:
            from collections import defaultdict
            import yaml
        except ModuleNotFoundError:
            logger.exception("error when trying to load module yaml")
            raise 
                
        yaml.SafeDumper.add_representer(defaultdict,yaml.representer.Representer.represent_dict)
        cwd = os.getcwd()
        with open(os.path.join(cwd, f'{discover.package}.yaml'), 'w', encoding = 'utf-8') as file:
            for dct in discover:
                module_name = list(dct)[0]
                print(f'Parsing: \033[1;38;5;10m{module_name!r}\033[0m')
                yaml.safe_dump(dct, file)
        
    

class JSONExporter:
    def  export(self, discover: EngineProtocol): 
        logger.info(f'JSONExporter chosen.')
        import json
        
        
        dirpath = os.path.join(os.getcwd(), f'{discover.package}')
        os.makedirs(dirpath, exist_ok = True)
        for dct in discover:
            module_name, *_ = dct
            print(f'Parsing: \033[1;38;5;10m{module_name!r}\033[0m')
            fdr = ".".join(module_name.split(".")[:2])
            os.makedirs(os.path.join(dirpath, fdr), exist_ok=True)
            with open(os.path.join(dirpath, fdr, f'{module_name}.json'), 'w', encoding = 'utf-8') as f:
                json.dump(dct,f)

         
class SqliteExporter:
    def export(self, discover: EngineProtocol):
        logger.info(f'Sqlitexporter chosen.')
        import sqlite3 

        logger.debug("creating table")
        cwd = os.getcwd()
        conn = sqlite3.connect(os.path.join(cwd, f'{discover.package}.sqlite'))
        cursor = conn.cursor()

        cursor.executescript("""
        DROP TABLE IF EXISTS modules;
        CREATE TABLE modules(
            id INTEGER PRIMARY KEY,
            name TEXT);

        DROP TABLE IF EXISTS classes;
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

        DROP TABLE IF EXISTS bases;
        CREATE TABLE bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER REFERENCES classes(id),
            name TEXT);

        DROP TABLE IF EXISTS functions;
        CREATE TABLE functions (
            id INTEGER PRIMARY KEY ,
            module_id INTEGER REFERENCES modules(id),
            name TEXT,
            is_decorated INTEGER,
            is_async INTEGER,
            is_generator INTEGER,
            has_generator_delegation INTEGER);
        
        DROP TABLE IF EXISTS methods;
            CREATE TABLE methods (
            id INTEGER PRIMARY KEY ,
            class_id INTEGER REFERENCES classes(id),
            name TEXT,
            is_decorated INTEGER,
            is_async INTEGER,
            is_generator INTEGER,
            has_generator_delegation INTEGER);

        DROP TABLE IF EXISTS decorators;
        CREATE TABLE decorators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER REFERENCES classes(id),
            function_id INTEGER REFERENCES functions(id),
            method_id INTEGER REFERENCES methods(id),
            name TEXT);

        DROP TABLE IF EXISTS constants;                     
        CREATE TABLE constants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER REFERENCES modules(id),
            name TEXT,
            type TEXT -- 'constant' | 'variable'
        );
                             
        DROP TABLE IF EXISTS imports;
        CREATE TABLE imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER REFERENCES modules(id),
            source TEXT,   -- null for direct imports
            name TEXT,
            alias TEXT,
            type  TEXT-- 'direct' | 'external' | 'internal_absolute' | 'internal_relative'
        );
        CREATE INDEX idx_imports_name ON imports(name);
        CREATE INDEX idx_functions_name ON functions(name);
        CREATE INDEX idx_methods_name ON methods(name);
        CREATE INDEX idx_classes_name ON classes(name);
        CREATE INDEX idx_functions_module ON functions(module_id);
        CREATE INDEX idx_classes_module ON classes(module_id);
        CREATE INDEX idx_methods_class ON methods(class_id);
        """)
        logger.debug('Finished creating table')
        class_id = 0 
        func_id = 0
        method_id = 0
        for idx, dct in enumerate(discover, start = 1):
            module_name = list(dct)[0]
            print(f'Parsing: \033[1;38;5;10m{module_name!r}\033[0m')
            cursor.execute("INSERT INTO modules VALUES(?,?)", (idx,module_name))
            class_insert_stmt = """INSERT INTO classes (id, module_id, name, is_descriptor, 
                               descriptor_type, is_nested, metaclass, parent_class, has_metaclass,
                               is_contextmanager,is_iterable,is_iterator)
                               VALUES 
                               (:id, :module_id, :name, :is_descriptor, :descriptor_type,
                               :is_nested, :metaclass,
                               :parent_class, :has_metaclass,:is_contextmanager,
                               :is_iterable, :is_iterator)"""
            bases_stmt = """INSERT INTO bases(class_id, name) VALUES (:class_id, :name)"""
            decorator_stmt = """INSERT INTO decorators(class_id, function_id, method_id,name) VALUES 
                            (:class_id, :function_id, :method_id,:name)"""
            functions_stmt = """INSERT INTO functions 
                (id, module_id, name, is_async, is_generator, has_generator_delegation, is_decorated) VALUES
                (:id, :module_id, :name, :is_async, :is_generator, :has_generator_delegation, :is_decorated)"""
            methods_stmt = """INSERT INTO methods
                (id, class_id, name, is_async, is_generator, has_generator_delegation, is_decorated) VALUES
                (:id, :class_id, :name, :is_async, :is_generator, :has_generator_delegation, :is_decorated)"""
            
            for class_name, cls in dct[module_name]["classes"].items():
                class_id += 1
                cursor.execute(class_insert_stmt,{"id": class_id, "module_id": idx, 
                    "name": class_name,
                    "is_descriptor": int(cls["is_descriptor"]), 
                    "descriptor_type": cls.get("descriptor_type"),
                    "is_nested": int(cls["is_nested"]), 
                    "parent_class": cls["parent_class"],
                    "has_metaclass": int(cls["metadata"]["has_metaclass"]),
                    "is_contextmanager": int(cls["is_contextmanager"]),
                    "is_iterable": int(cls["is_iterable"]),
                    "is_iterator": int(cls["is_iterator"]),
                    "metaclass": cls["metadata"]["attrs"].get("metaclass")})
                cursor.executemany(bases_stmt,[
                               {"class_id": class_id, "name": base}
                               for id, base in enumerate(cls["bases"], start = 1)])
                cursor.executemany(decorator_stmt,[
                               {"class_id": class_id, "function_id": None, "method_id":None,"name": dec}
                               for id, dec in enumerate(cls["decorators"], start = 1)])
                
                for method_name, method in cls["methods"].items():
                    method_id += 1
                    cursor.execute(methods_stmt,
                    {"id": method_id, "class_id": class_id, "name": method_name, 
                     "is_async": int(method["is_async"]),
                     "is_generator": int(method["is_generator"]), 
                     'is_decorated': int(method['is_decorated']),
                     "has_generator_delegation": int(method["has_generator_delegation"])})
                
                    cursor.executemany(decorator_stmt, 
                                [{"class_id": None, "function_id": None,"method_id": method_id, "name": dec}
                                    for dec in method["decorators"]
                                ])

                
            
            for func_name, func in dct[module_name]["functions"].items():
                
                func_id += 1
                cursor.execute(functions_stmt,
                    {"id": func_id, "module_id": idx, "name": func_name, 
                     "is_async": int(func["is_async"]),
                     "is_generator": int(func["is_generator"]), 
                     'is_decorated': int(func['is_decorated']),
                     "has_generator_delegation": int(func["has_generator_delegation"])})
                
                cursor.executemany(decorator_stmt, 
                               [{"class_id": None, "function_id": func_id, "method_id":None,"name": dec}
                                   for dec in func["decorators"]
                               ])
            cursor.executemany("""INSERT INTO constants(module_id,name,type)
                               VALUES(:module_id, :name, :type)""",
                               [{"module_id": idx, "name": cnst,
                                 "type": {"constants":"constant","variables": "variable"}[cnst_type]}
                                   for cnst_type, consts in dct[module_name]["constants"].items()
                                   for cnst in consts
                               ])
            
            import_stmt = """INSERT INTO imports(module_id, source, name, alias,type)
            VALUES(:module_id, :source, :name, :alias,:type)"""
            
            
            cursor.executemany(import_stmt,[
                {"module_id": idx, "source": None, 
                "name": (m_name := x.split(" as "))[0].strip(), 
                "alias": m_name[-1].strip() if len(m_name) > 1  else None,
                "type": "direct"}
                for x in dct[module_name]["imports"]["direct"]
            ])

            cursor.executemany(import_stmt,[
                {"module_id": idx, "source": src, 
                 "name": (m_name := name.split(" as "))[0].strip(), 
                "alias": m_name[-1].strip() if len(m_name) > 1  else None, 
                 "type": "internal_absolute" if src == discover.package else "external"
                }
                for src, names in dct[module_name]["imports"]["external_imports"].items()
                for name in names
            ])
            
            cursor.executemany(import_stmt,[
                {"module_id": idx, "source": src, 
                 "name": (m_name := name.split(" as "))[0].strip(), 
                "alias": m_name[-1].strip() if len(m_name) > 1  else None, 
                 "type": {"absolute_imports": "internal_absolute",
                          "relative_imports": "internal_relative"}[type]
                }
                for type, imp_dct in dct[module_name]["imports"][discover.package].items()
                for src, names in imp_dct.items()
                for name in names
            ])

        cursor.executescript("""DROP VIEW IF EXISTS api_surface;
        create view api_surface as
        with cls_name AS ( 
            select m.id as mid, count(c.id) as cls_count from classes c
            join modules m on m.id = c.module_id 
            group by mid 
        ),
        func_name AS (
            select m.id as mid, count(f.id) as func_count from functions f 
            join modules m on m.id = f.module_id 
            group by mid 
        ), imp_name AS (
            select m.id as mid, count(imp.id) as imp_count from imports imp 
            join modules m on m.id = imp.module_id 
            group by mid 
        ), cnst_name AS (
            select m.id as mid, count(cnst.id) as cnst_count from constants cnst
            join modules m on m.id = cnst.module_id 
            group by mid 
        ), meth_name AS (
            select m.id as mid, count(md.id) as meth_count from methods md
            join classes c on c.id = md.class_id
            join modules m on m.id = c.module_id 
            group by mid 
        )	

        select m.name, 
            coalesce(cls_count,0) as cls_count,
            coalesce(meth_count,0) as meth_count,
            coalesce(func_count,0) as func_count, 
            coalesce(imp_count,0) as imp_count, 
            coalesce(cnst_count,0) as cnst_count, 
            coalesce(cls_count,0) + coalesce(meth_count,0) + coalesce(func_count,0) + coalesce(imp_count,0) + coalesce(cnst_count,0) as total 
        from modules m 
        left join cls_name on m.id = cls_name.mid 
        left join func_name on m.id = func_name.mid 
        left join imp_name on m.id = imp_name.mid 
        left join cnst_name on m.id = cnst_name.mid
        left join meth_name on m.id = meth_name.mid;""")
        
        
        cursor.executescript("""DROP VIEW IF EXISTS inheritance;
        create view inheritance AS 
        with class_cte AS (
            select 
                c.id, m.name||'.'||c.name as name 
            from classes c 
            join modules m 
                on m.id = c.module_id
        ),inht AS (
            select b.name as ancestor,
                c.name as child,
                b.name || '->' ||c.name as path,
                1 as lvl

            from bases b 
            join class_cte c on b.class_id = c.id
            
            UNION ALL
            select 
                i.ancestor,
                c.name as child, 
                path || '->' || c.name as path, 
                1+lvl as lvl
            
            from bases b 
            join inht i 
                on b.name = i.child 
            join class_cte c 
                on b.class_id = c.id
        )

        select ancestor,child, path, lvl from inht
        order by lvl desc;""")
        cursor.close()
        conn.commit()
        conn.close()
                

