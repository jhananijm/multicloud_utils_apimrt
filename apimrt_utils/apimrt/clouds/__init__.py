import os
import importlib
import pkgutil


def find_modules(package_name):
    modules = []
    for _, module_name, ispkg in pkgutil.walk_packages(package_name.__path__, package_name.__name__ + "."):
        try:
            if ispkg:
                modules += find_modules(importlib.import_module(module_name))
            else:
                modules.append(importlib.import_module(module_name))
        except ModuleNotFoundError:   # It will not load other cloud modules because of missing dependencies
            pass

    return modules

for module in find_modules(__import__(__name__, fromlist=["*"])):
    globals()[module.__name__] = module

