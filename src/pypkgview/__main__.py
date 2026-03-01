import argparse 
from . import (ModuleWalker, 
               Discover,JSONExporter, 
               YamlExporter,
               SqliteExporter, StreamExporter)
from .datastructures import Exporter

args = argparse.ArgumentParser("pypkgview")
args.add_argument('--module-path','-m')
args.add_argument('--output','-o',choices = ["json","yaml","sqlite"])
parser = args.parse_args()

discover = Discover(file_path = parser.module_path, module_walker_type = ModuleWalker)
exporter: Exporter = {
    "json": JSONExporter, 
    "yaml": YamlExporter, 
    "sqlite": SqliteExporter
}.get(parser.output,StreamExporter)
exporter().export(discover = discover)
