import ast
import logging
from .datastructures import Class, Callable 

logger = logging.getLogger(__name__)

class NodeVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.classes: list[Class] = []
        self._classes_stack: list[Class] = [] 
        self._functions_stack: list[ast.FunctionDef] = []
        self.functions: list[ast.FunctionDef] = []
        self.imports: list[ast.Import] = []
        self.import_froms: list[ast.ImportFrom] = []
        self.variables: list[ast.Assign] = []
        logger.debug('NodeVisitor initalized.')

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        logger.debug('visit_ClassDef called.')
        
        cls = Class(name = node.name, bases = node.bases, keywords = node.keywords, decorator_list = node.decorator_list,
                is_nested_class = bool(self._current_class) or bool(self._current_function))
        logger.debug(f'{cls} initalized.')

        logger.debug(f'{self._current_class}')
        if self._current_class is not None:
            cls.parent_class = self._current_class.name
        if self._current_function is not None:
            cls.parent_function = self._current_function.name

        self.classes.append(cls)
        self._classes_stack.append(cls)
        self.generic_visit(node)
        self._classes_stack.pop()

    @property
    def _current_class(self) -> Class | None:
        logger.debug(f'{self._classes_stack = !r}')
        return self._classes_stack[-1] if self._classes_stack else None
    
    @property
    def _current_function(self) -> Callable |None:
        logger.debug(f'{self._functions_stack = !r}')
        return self._functions_stack[-1] if self._functions_stack else None
        

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        logger.debug('visit_FunctionDef called.')

        func = Callable(name = node.name,decorator_list = node.decorator_list, 
                            is_async = isinstance(node,ast.AsyncFunctionDef),
                            is_nested = bool(self._current_function)
                            )
        if self._current_function is not None:
            func.parent_function = self._current_function.name
            
        is_method = self._current_class is not None 
        logger.debug(f'{node.name!r} is method {is_method!r}')
        
        if is_method:
                
            if node.name in ["__get__","__set__", "__delete__"]:
                self._current_class.is_descriptor = True 
                logger.debug(f'{node.name!r} is a descriptor True')
                match node.name:
                    case "__set__" | "__delete__":
                        self._current_class.descriptor_type = "data"
                    case "__get__":
                        if self._current_class.descriptor_type is None: 
                            self._current_class.descriptor_type = "non_data"
            self._current_class.methods.append(func)


        else:
            self.functions.append(func)

        self._functions_stack.append(func) 
        self.generic_visit(node)
        self._functions_stack.pop()
        
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.import_froms.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._current_class is None and self._current_function is None:
            self.variables.append(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        func = self._current_function 
        if func is None:
            return
        func.exceptions.append(node)
    
    def visit_Yield(self, node):
        func = self._current_function 
        func.is_generator = True 

    def visit_YieldFrom(self, node):
        func = self._current_function 
        func.has_generator_delegation = True
        
            