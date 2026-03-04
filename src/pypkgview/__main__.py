import argparse
import logging  
from . import (ModuleWalker, 
               Discover,JSONExporter, 
               YamlExporter,
               SqliteExporter, StreamExporter)
from .datastructures import Exporter


args = argparse.ArgumentParser("pypkgview")
args.add_argument('--module-path','-m', required = True)
args.add_argument('--output','-o',choices = ["json","yaml","sqlite"])
args.add_argument('--verbose','-v',action='store_true')
parser = args.parse_args()

if parser.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


logger.debug(f'{parser = !r}')

discover = Discover(file_path = parser.module_path, module_walker_type = ModuleWalker)

logger.info('Discover initalized.')

exporter: Exporter = {
    "json": JSONExporter, 
    "yaml": YamlExporter, 
    "sqlite": SqliteExporter
}.get(parser.output,StreamExporter)

logger.info(f'Exporter: {exporter.__class__.__name__!r} initalized')

exporter().export(discover = discover)
