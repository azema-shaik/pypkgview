import argparse
import logging  
from . import (ModuleWalker, 
               Discover,JSONExporter, 
               YamlExporter,
               SqliteExporter, StreamExporter)
from .datastructures import Exporter
from .render import extractor


parser = argparse.ArgumentParser("pypkgview",description = "Understand any Python package before you touch it.")

subparser = parser.add_subparsers(dest = "command",required = True)

exporter = subparser.add_parser("export",
    help="Export package analysis to json, yaml or sqlite",
    description="Walk a Python package and export extracted analysis data.")
exporter.add_argument('--module-path','-m', required = True)
exporter.add_argument('--exporter','-e',choices = ["json","yaml","sqlite"])
exporter.add_argument('--verbose','-v',action='store_true')

dashboard = subparser.add_parser("dashboard",
    help="Generate an HTML dashboard from package analysis",
    description="Analyze a package and render an interactive HTML dashboard."
)
dashboard.add_argument('--module-path','-m', required = True)
dashboard.add_argument('--verbose','-v',action='store_true')


args = parser.parse_args()

if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


logger.debug(f'{parser = !r}')

discover = Discover(file_path = args.module_path, module_walker_type = ModuleWalker)

logger.info('Discover initalized.')

logger.info(f'Command initialized: {args.command!r}')
match args.command:
    case "export":
        print(f"Exporter \033[1;38;5;9mExporting to {args.exporter!r}.\033[0m")
        exporter: Exporter = {
            "json": JSONExporter, 
            "yaml": YamlExporter, 
            "sqlite": SqliteExporter
        }.get(args.exporter,StreamExporter)

        logger.info(f'Exporter: {exporter.__class__.__name__!r} initalized')
        exporter().export(discover = discover)
        print(f"\033[1;38;5;9mExporting to {args.exporter!r} is complete\033[0m")
    
    case "dashboard":
        print(f"Dashboard: \033[1;38;5;9mExporting data to sqlite exporter.\033[0m")
        SqliteExporter().export(discover = discover)
        extractor(discover.package)
    case _:
        print(f"\033[38;5;11m[WARNING] Select a valid option\033[0m")


