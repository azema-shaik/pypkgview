import os 
import logging
from typing import Generator
from .walker import BaseModuleWalker, ModuleWalker


logger = logging.getLogger(__name__)
class DiscoverEngine:
    def __init__(self, file_path: str, module_walker_type: BaseModuleWalker,
                 ignore_syntax_errors = True):
        self.file_path = file_path 
        self._package = os.path.split(file_path)[-1]
        self.walker = module_walker_type 
        self.ignore_syntax_error = ignore_syntax_errors

    @property
    def package(self):
        return self._package

    def __iter__(self):
        for dirpath, folders, files in os.walk(self.file_path):
            if dirpath.endswith("__pycache__"):
                continue 
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = os.path.join(dirpath,file)
                module_name = full_path.replace(self.file_path,self.package).replace(os.sep,".").replace(".py","").replace("__init__","").strip(" .")
                m = self.walker(module_name = module_name, module_path = full_path)
                try:
                    dct = m()
                except SyntaxError as e:
                    if not self.ignore_syntax_error:
                        raise e
                    logger.exception(f'Error when trying to parse module')
                    dct = {}

                yield {module_name:dct}