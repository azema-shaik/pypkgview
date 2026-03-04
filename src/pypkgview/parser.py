import ast
import logging
from .datastructures import Class 

logger = logging.getLogger(__name__)

class NodeVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.classes: list[Class] = []
        self._classes_stack: list[Class] = [] 
        self.functions: list[ast.FunctionDef] = []
        self.imports: list[ast.Import] = []
        self.import_froms: list[ast.ImportFrom] = []
        self.variables: list[ast.Assign] = []
        logger.debug('NodeVisitor initalized.')

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        logger.debug('visit_ClassDef called.')
        
        cls = Class(name = node.name, bases = node.bases, keywords = node.keywords, decorator_list = node.decorator_list,
                is_nested_class = bool(self._current_class))
        logger.debug(f'{cls} initalized.')

        logger.debug(f'{self._current_class}')
        if self._current_class is not None:
            cls.parent_class = self._current_class.name
        self.classes.append(cls)
        self._classes_stack.append(cls)
        self.generic_visit(node)
        self._classes_stack.pop()

    @property
    def _current_class(self) -> Class | None:
        logger.debug(f'{self._classes_stack = !r}')
        return self._classes_stack[-1] if self._classes_stack else None
        

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        logger.debug('visit_FunctionDef called.')

        is_method = self._current_class is not None 
        logger.debug(f'{node.name!r} is method {is_method!r}')
        
        if is_method:
            method_type = list(filter(
                lambda x: x in ["staticmethod", "property", "classmethod", "setter", "deleter"],
                map(lambda x: getattr(x,{ast.Name:"id", ast.Attribute: "attr"}.get(x.__class__)) if not isinstance(x,ast.Call) else "", 
                    node.decorator_list)
                ))
            
            logger.debug(f'{method_type = !r}')

            match method_type:
                
                case []:
                    self._current_class.method.append(node)
                case ["staticmethod"]:
                    self._current_class.staticmethod.append(node)
                case ["classmethod"]:
                    self._current_class.classmethod.append(node)
                case ["property" | "setter" | "deleter"]:
                    self._current_class.property.append(node)
                
            if node.name in ["__get__","__set__", "__delete__"]:
                self._current_class.is_descriptor = True 
                logger.debug(f'{node.name!r} is a descriptor True')
                match node.name:
                    case "__set__" | "__delete__":
                        self._current_class.descriptor_type = "data"
                    case "__get__":
                        if self._current_class.descriptor_type is None: 
                            self._current_class.descriptor_type = "non_data"


        else:
            self.functions.append(node)
        
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.import_froms.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._current_class is None:
            self.variables.append(node)