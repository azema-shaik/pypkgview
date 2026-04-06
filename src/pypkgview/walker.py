import os 
import ast 
import pathlib 
import builtins
import logging
import tokenize
from typing import Literal 
from collections import defaultdict
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .datastructures import Class, Callable 
from .parser import NodeVisitor 


logger = logging.getLogger(__name__)

@dataclass(frozen = True)
class _Name:
    name: str 
    imp_type: Literal["direct","import_from"]
    alias: str | None = None 


class BaseModuleWalker(ABC):
    def __init__(self, *, module_name: str, module_path: str):
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"{module_path!r} does not exist in the file system")
        if not os.path.isabs(module_path):
            raise ValueError(f"{module_path!r} must be an absolute path")
        
        self.module_name = module_name 
        self._modules = self.module_name.split(".")
        self.package = self._modules[0]
        self.module_path = pathlib.Path(module_path)

    def _handle_import_name_resolution(self, imp: ast.ImportFrom):
        
        if imp.level == 0:
            return imp.module
        p = '.'.join(mod for mod in self._modules[:-imp.level]) + ("."+imp.module if imp.module is not None else "")
        logger.debug(f'imported name: {p}')
        return p

        

    def _parse_import_from(self, imports: list[ast.ImportFrom]) -> dict[str, str | dict[str, str | list[str]]]:
        logger.debug('_parse_import_from running')

        other_imports = defaultdict(list)
        current_package = {"relative_imports": defaultdict(list), "absolute_imports": defaultdict(list)}
        memory = {}
        logger.debug('memory dict initialized')

        logger.debug(f'number of imports = {len(imports)}')
        
        for idx,imp in enumerate(imports,start = 1):
            logger.debug(f'memory dict at the beginning of iteration({idx}) {memory = }')
            logger.debug(f'{imp.__dict__}')    
            
            imported_from = self._handle_import_name_resolution(imp)
            logger.debug(f'{imported_from = !r}')
            
            imports = [(name.name if name.asname is None else f"{name.name} as {name.asname}") for name in imp.names] 
            logger.debug(f'{imports = !r} {"relative_imports" if imp.level > 0 else "absolute_imports"}')
            
            memory |= {(name.asname or name.name): _Name(name = f'{imported_from}.{name.name}', alias = name.asname,imp_type = 'import_from') 
                                                         for name in imp.names}
            logger.debug(f'memory dict at the end of iteration({idx}) {memory = }')
            
            if imp.level > 0 or imp.module == self.package or imported_from.split('.')[0] == self.package:
                current_package[("relative_imports" if imp.level > 0 else "absolute_imports")][imported_from].extend(imports)
            else:
                other_imports[imported_from].extend(imports) 
        
        logger.debug(f'"from import" processing complete. Memory {memory}')
        return {self.package: current_package, 
                "external_imports": dict(other_imports)}, memory
    
    def _parse_imports(self, imports: list[ast.Import], memory) -> list[str]:
        logger.debug('_parse_imports')
        results = []
        for imp in imports:
            for name in imp.names:
                results += [(name.name if name.asname is None else f"{name.name} as {name.asname}")]
                memory[name.asname or name.name] = _Name(name = name.name, alias = name.asname, imp_type = 'direct')
        
        logger.debug(f'Memory: {memory}')        
        return results
    
    def _parse_keywords(self, cls: Class, memory) -> dict[str, bool | str]:
        attrs = {k.arg : ast.unparse(k.value)
            for k in cls.keywords}
        if "metaclass" in attrs:
            attrs["metaclass"] = self._handle_name_resolution(attrs["metaclass"],memory)
            

        return {"has_metaclass": ("metaclass" in attrs), "attrs": attrs}
    
    def _parse_exceptions(self, exceptions: list[ast.Raise],memory):
        excs = []
        for exception in exceptions:
            if not isinstance(exception.exc, ast.Call):
                continue 
            exception = ast.unparse(exception.exc.func)
            excs += [self._handle_name_resolution(exception, memory)]
        return excs




    def _parse_class(self, classes: list[Class], memory) -> dict[str, list[str] | bool | dict[str, bool | str ]]:
        clss_dct = {}
        for cls in classes:
            bases = []
            for base in cls.bases:
                if isinstance(base, ast.Call):
                    base = base.func
                if isinstance(base, ast.Subscript):
                    base = base.value
                b = ast.unparse(base)
                b = self._handle_name_resolution(b, memory)
                bases += [b]
            clss_dct[cls.name] = {"bases": bases, 
                                  "decorators": self._handle_decorator(cls, memory), 
                                  'is_contextmanager': self._parse_context_manager(cls.methods),
                                  'methods': self._parse_function(cls.methods,memory),
                                  'is_nested': cls.is_nested_class, 
                                  'parent_class': cls.parent_class,
                                  'parent_function': cls.parent_function,
                                  "is_descriptor":cls.is_descriptor,
                                  "is_iterator": self._parse_iterator(cls.methods),
                                  'is_iterable': self._parse_iterable(cls.methods),
                                  "metadata": self._parse_keywords(cls, memory)} | ({"descriptor_type": cls.descriptor_type} if cls.is_descriptor else {})
        return dict(clss_dct)
    
    def _parse_context_manager(self, nodes: list[ast.FunctionDef | ast.AsyncFunctionDef]):
        return any((x.name == '__enter__') for x in nodes) and \
                any((x.name == '__exit__') for x in nodes)
    
    def _parse_iterator(self, nodes: list[ast.FunctionDef | ast.AsyncFunctionDef]):
        return any((x.name == '__iter__') for x in nodes) and \
                any((x.name == '__next__') for x in nodes)
    
    def _parse_iterable(self, nodes: list[ast.FunctionDef | ast.AsyncFunctionDef]):
        return any((x.name == '__iter__') for x in nodes)
    
    def _handle_name_resolution(self,name: str, memory):
        logger.debug(f'naming resolution bases or decorators. Resolving {name = !r}')
        try:
            logger.debug(f"memory for resolving name: {memory=}")
            key = name.split('.',maxsplit = 1)
            mem_value: _Name = memory[key[0]]
            
            logger.debug(f'{mem_value!r} extracted from memory')       
            attr = name.split('.',maxsplit=1)[-1]
            name = (f'{mem_value.name}')+(f'.{attr}' if len(key) == 2 else '')
            logger.debug(f'Resolved name: {name}')
        except KeyError as e: 
            if hasattr(builtins,name):
                logger.debug(f'{name!r} is a builtins')
                name = f'builtins.{name}'
            else:
                logger.debug(f'{name!r} neither in imports dict nor a builtin. Meaning {name!r} defined in current module.')
                name = f'{self.module_name}.{name}'
        
        logger.info(f'Final Resolved name: {name!r}')
        return name

    
    def _handle_decorator(self, func: ast.FunctionDef|Class, memory: dict[str,str]) -> list[str]:
        logger.debug(f'Handling decorators')

        decs = []
        for dec in func.decorator_list:
            if isinstance(dec, ast.Call):
                dec = dec.func
            name = ast.unparse(dec)
            
            logger.debug(f'Extracted decorator name: {name!r}')
            name = self._handle_name_resolution(name, memory)
            decs.append(name)
        logger.debug(f'{decs = }')
        return decs
    
    def  _parse_function(self,functions: list[Callable], memory: dict[str,str]) -> dict[str, dict[str,str|bool] | list[str] | bool]:
        funcs = {}
        for func in functions:
            decs = self._handle_decorator(func, memory)
            funcs[func.name] = {"is_async": func.is_async,
                                "is_decorated": bool(decs), "decorators": decs, 
                                "is_nested": func.is_nested, "parent_function": func.parent_function,
                                "is_generator": func.is_generator, "has_generator_delegation": func.has_generator_delegation,
                                "exceptions": self._parse_exceptions(func.exceptions,memory)}
        return funcs
    
    def _parse_constants(self, vars: list[ast.Assign]) -> dict[str,list[str]]:
        constants = []
        variable_declarations = []

        for var in vars:
            for tar in var.targets:

                if isinstance(var.value, ast.Constant):
                    constants += [ast.unparse(tar)]  if not isinstance(tar, ast.Tuple) else [ast.unparse(t) for t in tar.elts]
                else:
                    variable_declarations += [ast.unparse(tar)]  if not isinstance(tar, ast.Tuple) else [ast.unparse(t) for t in tar.elts]
        return {"constants": constants, "variables": variable_declarations}
    
    @abstractmethod
    def parser(self) -> ast.NodeVisitor: ...

    @abstractmethod
    def __call__(self): ...


class ModuleWalker(BaseModuleWalker):

    def parser(self):
        logger.info(f'Parsing module. Module {self.module_name}')
        encoding, _ = tokenize.detect_encoding(open(self.module_path, mode = 'rb').readline)
        logger.debug(f'Detected encoding: {encoding}')

        try:
            code = ast.parse(self.module_path.read_text(encoding = encoding) )
        except SyntaxError as e:
            raise SyntaxError(f'error when trying to parse {self.module_path!r}.{e.args[0]}')
        
        logger.debug(f'NodeVisitor will be initialized.')

        v = NodeVisitor()

        logger.debug(f'node will be visited.')
        v.visit(code)
        return v         
    
    def __call__(self):
        v: NodeVisitor = self.parser()
        main_dct = {}
        logger.debug("Parsing starts.")
        relative_imports, memory = self._parse_import_from(v.import_froms)
        main_dct["imports"] = {"direct": self._parse_imports(v.imports,memory)}|relative_imports
        main_dct["classes"] = self._parse_class(v.classes, memory)
        main_dct["functions"] = self._parse_function(v.functions,memory)
        main_dct["constants"] = self._parse_constants(v.variables)
        return main_dct