import ast 
from typing import (
        Literal, 
        Protocol, 
        Iterator)
from dataclasses import dataclass, field 


@dataclass 
class Class:
    name: str 
    bases: list[ast.expr]
    keywords: list[ast.keyword]
    decorator_list: list[ast.expr]
    is_descriptor: bool = field(default = False, repr = False)
    descriptor_type: Literal["data","non_data"] | None = field(default = None, repr = False)
    method: list[ast.FunctionDef] = field(default_factory = list, repr = False)
    classmethod: list[ast.FunctionDef] = field(default_factory = list, repr = False)
    staticmethod: list[ast.FunctionDef] = field(default_factory = list, repr = False)
    property: list[ast.FunctionDef] = field(default_factory = list, repr = False)
    is_nested_class: bool = field(default = False, repr = False)
    parent_class: str| None = field(default = None, repr = True)



class Discover(Protocol):
    @property
    def package(self) -> str: ...
    def __iter__(self) -> Iterator[dict]: ...


class Exporter(Protocol):
    def  export(self, discover: Discover) -> None: ...