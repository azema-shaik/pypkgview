import sys
import json
import logging
import sqlite3
import pathlib 
import pprint
from jinja2 import Environment, FileSystemLoader 


logger = logging.getLogger(__name__)

def classify_imports(package_name,cursor):
    profile = {"stdlib": 0,"internal": 0,"third_party":0}
    stdlib    = sys.stdlib_module_names 

    for name, count in cursor.fetchall():

        if name == package_name:
            profile["internal"] += count 
        
        elif name in stdlib:
            profile["stdlib"] += count
        else:
            profile["third_party"] += count 

    
    logger.debug(f'{profile = }')
    return profile 
        


def render_dashboard(data: dict, output_path: str):
    
    env = Environment(
        loader = FileSystemLoader(pathlib.Path(__file__).parent/'dashboard/templates')
    )

    d3js = pathlib.Path(pathlib.Path(__file__).parent/"dashboard/static/d3.min.js").read_text()
    
    template = env.get_template("dashboard.html")
    
    html = template.render(
        d3js_source = d3js,
        pkg_name = data["package_name"],
        stats = data["stats"],
        top_fanout = data["top_fanout"],
        top_fanin = data["top_fanin"],
        top_decorator = data["top_decorator"],
        top_base = data["top_base"],
        import_types = data["import_types"],
        external_imports = data["external_imports"],  
        internal_imports = data["internal_imports"],  
        decorators = data["decorators"],
        base_classes = data["base_classes"],
        class_traits = data["class_traits"],
        func_traits = data["func_traits"],
        hubs = data["hubs"],
        api_surface = data["api_surface"],
        inheritance_records = data["inheritance_records"],
        metaclass_records = data["metaclass_records"],
        method_traits = data["method_traits"],
        top_method_decorators = data["top_method_decorators"]

 
    )

    pathlib.Path(output_path).write_text(html,encoding = 'utf-8')
    print("Dashboard: \033[38;5;10mCompleted Dashboard printed\033[0m")

def extractor(package_name: str):
    queries: dict[str,str] = json.load(open(pathlib.Path(__file__).parent/"dashboard/query_lib.json"))
    
    results = {"package_name": package_name}
    logger.debug('Establishing connection to sqlite')
    conn = sqlite3.connect(f'{package_name}.sqlite')
    cursor = conn.cursor()

    print(f"Dashboard: \033[38;5;9mFetching Package Details\033[0m")
    logger.debug('Fetching Package Details')

    m,c,meth,f,cnst,imps = cursor.execute(queries["stats"]).fetchone()
    results["stats"] = {"modules":m, "classes":c,
                         "methods": meth,"functions":f,
                         "globals": cnst,"imports":imps}
    

    print(f"Dashboard: \033[38;5;9mFetching Import Details\033[0m")
    logger.debug('Fetching Import Details')

    fanout = cursor.execute(queries["fanout"],(f"{package_name}%",)).fetchone()
    results["top_fanout"] = {"module": fanout[0], "value": fanout[1]}

    fanin = cursor.execute(queries["fanin"],(f"{package_name}%",)).fetchone()
    results["top_fanin"] = {"module": fanin[0], "value": fanin[1]}

    print(f"Dashboard: \033[38;5;9mFetching Class Details\033[0m")
    logger.debug('Fetching Class Details')

    print(f"Dashboard: \033[38;5;9mFetching Decoratoe Details\033[0m")
    logger.debug('Fetching Decorator Details')

    decorator = cursor.execute(queries["decorator"]).fetchone()
    results["top_decorator"] = {"name": decorator[0], "count": decorator[1]}

    base = cursor.execute(queries["base"]).fetchone()
    results["top_base"] = {"name": base[0], "count": base[1]}

    print(f"Dashboard: \033[38;5;9mFetching Import Analysis\033[0m")
    logger.debug('Fetching Import Analysis')
    results["import_types"] = classify_imports(package_name,cursor.execute(queries["import_type"]))
    

    cursor.execute(queries["external_imports"],{'mod':f'{package_name}%'})

    results["external_imports"] = []
    for fname, count in cursor:
        results["external_imports"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Internal Imports\033[0m")
    logger.debug('Fetching Top Internal Imports')
    cursor.execute(queries["internal_imports"],{'mod':f'{package_name}%'})


    results["internal_imports"] = []
    for fname, count in cursor:
        results["internal_imports"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Inherited Classes\033[0m")
    logger.debug('Fetching Top Inherited Classes')
    cursor.execute(queries["top_bases"])

    results["base_classes"] = []
    for fname, count in cursor:
        results["base_classes"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Decorators\033[0m")
    logger.debug('Fetching Top Decorators')
    cursor.execute(queries["top_decorators"])

    results["decorators"] = []
    for fname, count in cursor:
        results["decorators"].append(
            {"name": fname, "count": count}
        )

    ###################################### HERE ################
    
    dec,ctx, descriptor, has_metaclass, iterable, iterator = cursor.execute(queries["class_traits"]).fetchone()
    results["class_traits"] = {
                    "decorated":    dec,
                    "contextmanager": ctx,
                    "descriptor":   descriptor,
                    "has_metaclass": has_metaclass,
                    "iterable":     iterable,
                    "iterator":     iterator,
                }
    print(f"Dashboard: \033[38;5;9mFetching Functions Details\033[0m")
    logger.debug('Fetching Functions Details')

    dec, gen, async_count = cursor.execute(queries["function_traits"]).fetchone()
    results["func_traits"] = {
        "decorated":   dec,
        "generator":   gen,
        "async_count": async_count,
    }

    print("Dashboard: \033[38;5;9mFetching Hub Analysis\033[0m")
    logger.debug("hub analysis")

    results["hubs"] = [{"module": module, "fanout": fanout, "fanin": fanin} 
        for module, fanout, fanin, _ in \
            cursor.execute(queries["hubs"] ,(f"{package_name}%",))]
    
    results["api_surface"] = [{"name": module, 
                        "cls_count": cls, "func_count": func, 
                        "imp_count":imp, "cnst_count": cnst, "total": total }
        for module,cls,method,func,imp,cnst,total in cursor.execute(queries["api_surface"])
    ]
    
    results["inheritance_records"] = [rec
        for rec in cursor.execute(queries["inheritance_records"])
    ]

    results["metaclass_records"] = [row[0] for row in cursor.execute(queries["metaclass_graph"])]
    
    dec, gen, async_count = cursor.execute(queries["method_traits"]).fetchone()
    results["method_traits"] = {
        "decorated":   dec,
        "generator":   gen,
        "async_count": async_count,
    }

    cursor.execute(queries["top_method_decorators"])

    results["top_method_decorators"] = []
    for fname, count in cursor:
        results["top_method_decorators"].append(
            {"name": fname, "count": count}
        )





    
    render_dashboard(results,f'{package_name}.html')
    cursor.close()
    conn.close()



    



    

    



    


    


    

    





    


# render_dashboard(
#     {"package_name": "torch",
#      "totals": {
#          "modules": 2113,
#          "classes": 4886,
#          "functions": 15030,
#          "globals": 10956,
#          "imports": 29620
#      },
#      "top_external_imports": [
#     {"name": "typing.Any",              "count": 720},
#     {"name": "typing.Optional",         "count": 525},
#     {"name": "collections.abc.Callable","count": 510},
#     {"name": "typing.Union",            "count": 366},
#     {"name": "logging",                 "count": 326},
#     {"name": "typing.TYPE_CHECKING",    "count": 294},
#     {"name": "functools",               "count": 291},
#     {"name": "collections.abc.Sequence","count": 238},
#     {"name": "os",                      "count": 234},
#     {"name": "__future__.annotations",  "count": 222},
# ],
# "top_internal_imports": [
#     {"name": "torch._C",                "count": 891},
#     {"name": "torch.nn.functional",     "count": 743},
#     {"name": "torch._tensor",           "count": 651},
#     {"name": "torch.autograd",          "count": 589},
#     {"name": "torch._utils",            "count": 498},
#     {"name": "torch.nn.modules",        "count": 445},
#     {"name": "torch._ops",              "count": 401},
#     {"name": "torch.fx",                "count": 387},
#     {"name": "torch._prims",            "count": 334},
#     {"name": "torch.distributed",       "count": 298},
#     ],
#     "top_bases": [
#     {"name": "nn.Module",           "count": 341},
#     {"name": "enum.Enum",           "count": 141},
#     {"name": "abc.ABC",             "count": 86},
#     {"name": "typing.NamedTuple",   "count": 77},
#     {"name": "autograd.Function",   "count": 71},
#     {"name": "builtins.Exception",  "count": 66},
#     {"name": "VariableTracker",     "count": 65},
#     {"name": "typing.Generic",      "count": 56},
#     {"name": "typing.Protocol",     "count": 40},
#     {"name": "HigherOrderOperator", "count": 37},
# ],
# "top_decorators": [
#     {"name": "dataclasses.dataclass",     "count": 738},
#     {"name": "out_wrapper",               "count": 331},
#     {"name": "register_decomposition",    "count": 330},
#     {"name": "_onnx_symbolic",            "count": 319},
#     {"name": "contextlib.contextmanager", "count": 259},
#     {"name": "register_meta",             "count": 248},
#     {"name": "parse_args",                "count": 188},
#     {"name": "register_lowering",         "count": 177},
#     {"name": "functools.cache",           "count": 145},
#     {"name": "fx.compatibility",          "count": 133},
# ],
# "top_bases": [
#     {"name": "nn.Module",            "count": 341},
#     {"name": "enum.Enum",            "count": 141},
#     {"name": "abc.ABC",              "count": 86},
#     {"name": "typing.NamedTuple",    "count": 77},
#     {"name": "autograd.Function",    "count": 71},
#     {"name": "builtins.Exception",   "count": 66},
#     {"name": "VariableTracker",      "count": 65},
#     {"name": "typing.Generic",       "count": 56},
#     {"name": "typing.Protocol",      "count": 40},
#     {"name": "HigherOrderOperator",  "count": 37},
# ],
# "top_decorators": [
#     {"name": "dataclasses.dataclass",      "count": 738},
#     {"name": "out_wrapper",                "count": 331},
#     {"name": "register_decomposition",     "count": 330},
#     {"name": "_onnx_symbolic",             "count": 319},
#     {"name": "contextlib.contextmanager",  "count": 259},
#     {"name": "register_meta",              "count": 248},
#     {"name": "parse_args",                 "count": 188},
#     {"name": "register_lowering",          "count": 177},
#     {"name": "functools.cache",            "count": 145},
#     {"name": "fx.compatibility",           "count": 133},
# ],
# "top_modules": [
#     {"name": "common_methods_invocations", "classes": 10,  "functions": 468, "globals": 19,  "imports": 168, "total": 665},
#     {"name": "_sfdp_pattern_16",           "classes": 0,   "functions": 0,   "globals": 504, "imports": 20,  "total": 524},
#     {"name": "torch._refs",                "classes": 0,   "functions": 292, "globals": 117, "imports": 61,  "total": 470},
#     {"name": "_inductor.lowering",         "classes": 0,   "functions": 270, "globals": 78,  "imports": 105, "total": 453},
#     {"name": "common_utils",               "classes": 34,  "functions": 163, "globals": 98,  "imports": 87,  "total": 382},
#     {"name": "_meta_registrations",        "classes": 1,   "functions": 315, "globals": 16,  "imports": 44,  "total": 376},
#     {"name": "_dynamo.utils",              "classes": 20,  "functions": 191, "globals": 53,  "imports": 109, "total": 373},
#     {"name": "_inductor.ir",               "classes": 96,  "functions": 36,  "globals": 16,  "imports": 128, "total": 276},
#     {"name": "decompositions",             "classes": 1,   "functions": 221, "globals": 6,   "imports": 38,  "total": 266},
#     {"name": "torch (root)",               "classes": 24,  "functions": 53,  "globals": 32,  "imports": 145, "total": 254},
# ],
#     "class_properties": {
#     "decorated":       1097,
#     "contextmanager":   127,
#     "nested":            57,
#     "has_metaclass":     28,
#     "iterable":          85,
#     "iterator":           8,
#     "descriptor":        10,
# },
# "func_properties": {
#     "decorated":        740,
#     "generator":         48,
#     "async":              3,
#     "generator_deleg":   18,
# },

#     }, 
#     "dashboard.html"   
# )