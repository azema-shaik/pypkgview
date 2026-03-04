import os
import logging 
from datetime import datetime
from .walker import ModuleWalker 
from .engine import DiscoverEngine as Discover 
from .exporters import (
    JSONExporter, 
    YamlExporter,
    SqliteExporter,
    StreamExporter
)


logger = logging.getLogger(__name__)

# Add a handler to the package logger so subloggers propagate to it
handler = logging.FileHandler(os.path.join(os.getcwd(),f'pypkgview_{int(datetime.now().timestamp())}.log'),mode = 'w')
handler.setFormatter(logging.Formatter("[%(asctime)s]: [%(module)s]: [%(levelname)s]: [%(funcName)s]: [%(lineno)d]: [%(message)s]"))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.info('pypkgview initialized.')