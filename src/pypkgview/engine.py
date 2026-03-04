import os 
import logging
from typing import Generator
from .walker import BaseModuleWalker, ModuleWalker


logger = logging.getLogger(__name__)

class DiscoverEngine:
    def __init__(self, file_path: str, module_walker_type: BaseModuleWalker,
                 ignore_syntax_errors = True):
        if not os.path.exists(file_path):
            logger.error(f'{file_path!r} does not exists')
            raise FileNotFoundError(f'{file_path!r} does not exist')
        
        self.file_path = file_path 
        self._package = os.path.split(file_path)[-1]
        self.walker = module_walker_type 
        self.ignore_syntax_error = ignore_syntax_errors

    @property
    def package(self):
        return self._package

    def __iter__(self):
        for dirpath, folders, files in os.walk(self.file_path):
            logger.debug(f"Directory Path: {dirpath!r}")
            
            if dirpath.endswith("__pycache__"):
                continue 
            for file in files:
                if not file.endswith(".py"):
                    logger.debug(f"{os.path.join(dirpath,file)!r} is not a python file.")
                    continue
                
                full_path = os.path.join(dirpath,file)
                logger.info(f'{full_path!r} will be processed.')

                module_name = os.path.splitext(full_path)[0]\
                                .replace(self.file_path,self.package)\
                                .replace(os.sep,".").replace("__init__","").strip(" .")
                logger.info(F'Module Path: {module_name}')
                logger.debug('Initializing debug.')

                m = self.walker(module_name = module_name, module_path = full_path)
                logger.debug(f'Walker initialzed')
                
                try:
                    dct = m()
                except SyntaxError as e:
                    if not self.ignore_syntax_error:
                        raise e
                    logger.exception(f'Error when trying to parse module')
                    dct = {}

                yield {module_name:dct}