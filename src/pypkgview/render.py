import sys
import json
import logging
import sqlite3
import pathlib 
from jinja2 import Environment, FileSystemLoader 


logger = logging.getLogger(__name__)

def classify_imports(package_name,imports):
    profile = {"stdlib": 0,"internal": 0,"third_party":0}
    stdlib    = sys.stdlib_module_names 

    for imp in imports:
        name = imp["name"]
        count = imp["count"]

        if name == package_name:
            profile["internal"] += count 
        
        elif name in stdlib:
            profile["stdlib"] += count
        else:
            profile["third_party"] += count 

    return profile 
        


def get_insights(package_name:str,totals: dict,import_details: list[dict[str,str]]) -> list[dict]:
    insights = []

    # class vs function ratio
    classes   = totals["classes"]
    functions = totals["functions"]
    ratio     = classes / functions if functions > 0 else 0

    if ratio > 2:
        insights.append({
            "title":  "OOP Heavy",
            "detail": f"{classes:,} classes vs {functions:,} functions — "
                      f"this package strongly favors class-based design.",
        })
    elif ratio < 0.5:
        insights.append({
            "title":  "Functional API",
            "detail": f"{functions:,} functions vs {classes:,} classes — "
                      f"this package is primarily a functional interface.",
        })

    import_profile = classify_imports(package_name,import_details)
    stdlib      = import_profile["stdlib"]
    internal    = import_profile["internal"]
    third_party = import_profile["third_party"]
    total       = stdlib + internal + third_party

    if total > 0:
        tp_pct  = round(third_party / total * 100)
        int_pct = round(internal    / total * 100)
        sb_pct  = round(stdlib      / total * 100)

        if tp_pct > 40:
            insights.append({
                "title":  "High External Dependency",
                "detail": f"{tp_pct}% of imports are third-party packages. "
                          f"This package relies heavily on external libraries."
            })
        elif int_pct > 60:
            insights.append({
                "title":  "Self-Contained",
                "detail": f"{int_pct}% of imports are internal. "
                          f"This package mostly depends on itself."
            })
        elif sb_pct > 50:
            insights.append({
                "title":  "Stdlib Reliant",
                "detail": f"{sb_pct}% of imports come from the standard library. "
                          f"Minimal external dependencies."
            })
    

    

    return insights,import_profile



def render_dashboard(data: dict, output_path: str):
    
    env = Environment(
        loader = FileSystemLoader(pathlib.Path(__file__).parent/'dashboard/templates')
    )

    chartjs = pathlib.Path(pathlib.Path(__file__).parent/"dashboard/static/chart.min.js").read_text()
    
    template = env.get_template("dashboard.html")
    insights,import_profile = get_insights(data["package_name"],data["totals"],data["first_imp_names"])
    html = template.render(
        chartjs_source = chartjs,
        package_name = data["package_name"],
        totals = data["totals"],
        insights = insights,
        top_external_imports=data["top_external_imports"],  
        top_internal_imports=data["top_internal_imports"],  
        top_decorators=data["top_decorators"],
        top_bases=data["top_bases"],
        top_modules=data["top_modules"],
        class_properties=data["class_properties"], 
        import_profile = import_profile,
    func_properties=data["func_properties"],  
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

    m,c,f,cnst,imps = cursor.execute(queries["Package Composition"]).fetchone()
    results["totals"] = {"modules":m, "classes":c,"functions":f,
                         "globals": cnst,"imports":imps}
    

    print(f"Dashboard: \033[38;5;9mFetching Class Details\033[0m")
    logger.debug('Fetching Class Details')
    
    dec,ctx,nes, met, itb, itr, dcpr = cursor.execute(queries["Class Details"]).fetchone()
    results["class_properties"] = {"decorated":dec, 
                                   "contextmanager":ctx, "nested":nes, 
                                   "has_metaclass": met, 
                                   "iterable": itb, "iterator": itr,
                                   "descriptor": dcpr}
    
    print(f"Dashboard: \033[38;5;9mFetching Functions Details\033[0m")
    logger.debug('Fetching Functions Details')

    dec, gen, asyc, gen_deg = cursor.execute(queries["Functions Details"]).fetchone()
    results["func_properties"] = {
        "decorated": dec, 
        "generator": gen,
        "async": asyc, 
        "generator_deleg": gen_deg
    }

    print("Dashboard: \033[38;5;9mFetching Top External Imports\033[0m")
    logger.debug('Fetching Top External Imports')
    cursor.execute(queries["Top External Imports"],{'mod':f'{package_name}%'})

    results["top_external_imports"] = []
    for fname, count in cursor:
        results["top_external_imports"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Internal Imports\033[0m")
    logger.debug('Fetching Top Internal Imports')
    cursor.execute(queries["Top Internal Imports"],{'mod':f'{package_name}%'})


    results["top_internal_imports"] = []
    for fname, count in cursor:
        results["top_internal_imports"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Inherited Classes\033[0m")
    logger.debug('Fetching Top Inherited Classes')
    cursor.execute(queries["Top Inherited Classes"])

    results["top_bases"] = []
    for fname, count in cursor:
        results["top_bases"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Top Decorators\033[0m")
    logger.debug('Fetching Top Decorators')
    cursor.execute(queries["Top Decorators"])

    results["top_decorators"] = []
    for fname, count in cursor:
        results["top_decorators"].append(
            {"name": fname, "count": count}
        )

    print("Dashboard: \033[38;5;9mFetching Modules Detail\033[0m")
    logger.debug('Fetching Modules Detail')
    cursor.execute(queries["god_modules"])

    results["top_modules"] = []
    for name, c, f,g,imp,total in cursor:
        results["top_modules"].append(
            {
                "name": name,
                "classes": c, "functions": f, 
                "globals":g, "imports":imp, "total":total
            }
        )





    logger.debug('Fetching first name of imports')
    cursor.execute(queries["_Import Split"],{'mod':f'{package_name}%'})
    results["first_imp_names"] = []

    for name,count in cursor:
        results["first_imp_names"].append(
            {"name": name, "count":count}
        )

    print(f'Dashboard: \033[1;38;5;10mComplete Fetching\033[0m')
    
    render_dashboard(results,f'{package_name}.html')



    



    

    



    


    


    

    





    


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