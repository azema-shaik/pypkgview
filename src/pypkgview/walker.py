import os 
import ast 
import pathlib 
import builtins
from collections import defaultdict 
from abc import ABC, abstractmethod

from .datastructures import Class 
from .parser import NodeVisitor 

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
        

    def _parse_import_from(self, imports: list[ast.ImportFrom]) -> dict[str, str | dict[str, str | list[str]]]:
        other_imports = defaultdict(list)
        current_package = {"relative_imports": {}, "absolute_imports": {}}
        memory = {}
        for imp in imports:
            
            imported_from = imp.module if imp.level == 0 else ((".".join(mod for mod in self._modules[:-imp.level]))+("."+imp.module if imp.module is not None else ""))
            imports = [(name.name if name.asname is None else f"{name.name} as {name.asname}") for name in imp.names] 
            memory |= {(name.asname or name.name): f'{imported_from}.{name.name}' for name in imp.names}
            
            
            if imp.level > 0 or imp.module == self.package or imported_from.split('.')[0] == self.package:
                current_package[("relative_imports" if imp.level > 0 else "absolute_imports")][imported_from] = imports
            else:
                other_imports[imported_from] = imports 
        
        
        return {self.package: current_package, "external_imports": dict(other_imports)}, memory
    
    def _parse_imports(self, imports: list[ast.Import]) -> list[str]:
        return [(name.name if name.asname is None else f"{name.name} as {name.asname}")
                for imp in imports for name in imp.names]
    
    def _parse_keywords(self, cls: Class, memory) -> dict[str, bool | str]:
        attrs = {k.arg : ast.unparse(k.value)
            for k in cls.keywords}
        if "metaclass" in attrs:
            try:
                attrs["metaclass"] = memory[attrs["metaclass"].split(".")[0]]
            except KeyError: ... 

        return {"has_metaclass": ("metaclass" in attrs), "attrs": attrs}

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
                                  'is_nested': cls.is_nested_class, 'parent_class': cls.parent_class,
                                  "is_descriptor":cls.is_descriptor,
                                  "metadata": self._parse_keywords(cls, memory)} | ({"descriptor_type": cls.descriptor_type} if cls.is_descriptor else {})
        return dict(clss_dct)
    

    def _parse_generator(self, node: ast.FunctionDef|ast.AsyncFunctionDef) -> dict[str, bool]:
        d = list(filter(lambda x: isinstance(x,(ast.Yield,ast.YieldFrom))
        ,ast.walk(node) ))
        return {"is_generator": any(isinstance(x, ast.Yield) for x in d), 
                "has_generator_delegation": any(isinstance(x, ast.YieldFrom) for x in d)
        }
    
    def _handle_name_resolution(self,name: str, memory):
        try:
            name = memory[name.split('.')[0]]
        except KeyError as e: 
            if hasattr(builtins,name):
                name = f'builtins.{name}'
            else:
                name = f'{self.module_name}.{name}'
        
        return name

    
    def _handle_decorator(self, func: ast.FunctionDef|Class, memory: dict[str,str]) -> list[str]:
        decs = []
        for dec in func.decorator_list:
            if isinstance(dec, ast.Call):
                dec = dec.func
            name = ast.unparse(dec)
            name = self._handle_name_resolution(name, memory)
            decs.append(name)
        return decs
    
    def  _parse_function(self,functions: list[ast.FunctionDef], memory: dict[str,str]) -> dict[str, dict[str,str|bool] | list[str] | bool]:
        funcs = {}
        for func in functions:
            decs = self._handle_decorator(func, memory)
            funcs[func.name] = {"is_async": isinstance(func, ast.AsyncFunctionDef),
                                "is_decorated": bool(decs), "decorators": decs} | self._parse_generator(func)
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
        try:
            code = ast.parse(self.module_path.read_text(encoding = "utf-8") )
        except SyntaxError as e:
            raise SyntaxError(f'error when trying to parse {self.module_path!r}')
        v = NodeVisitor()
        v.visit(code)
        return v         
    
    def __call__(self):
        v: NodeVisitor = self.parser()
        main_dct = {}
        relative_imports, memory = self._parse_import_from(v.import_froms)
        main_dct["imports"] = {"direct": self._parse_imports(v.imports)}|relative_imports
        main_dct["classes"] = self._parse_class(v.classes, memory)
        main_dct["functions"] = self._parse_function(v.functions,memory)
        main_dct["constants"] = self._parse_constants(v.variables)
        return main_dct