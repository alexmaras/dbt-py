"""
Shim the dbt CLI to include our custom modules.
"""
import importlib
import os
import pathlib
import pkgutil
import sys
from types import ModuleType
from typing import Any

import dbt.cli.main
import dbt.context.base
from dbt.context.base import get_context_modules as _get_context_modules

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
# Python-style ref, e.g. `package.module.submodule`
PACKAGE_ROOT: str = os.environ.get("DBT_PY_PACKAGE_ROOT", "custom")
# The name to associate with the package
PACKAGE_NAME: str = os.environ.get("DBT_PY_PACKAGE_NAME", PACKAGE_ROOT)


def import_submodules(
    package_name: str,
    recursive: bool = True,
) -> dict[str, ModuleType]:
    """
    Import all submodules of a module, recursively, including subpackages.

    - https://stackoverflow.com/a/25562415/10730311
    """
    package = importlib.import_module(package_name)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = f"{package.__name__}.{name}"
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results |= import_submodules(full_name)

    return results


def new_get_context_modules() -> dict[str, dict[str, Any]]:
    """
    Append the custom modules into the whitelisted dbt modules.
    """
    import_submodules(PACKAGE_ROOT)
    modules = _get_context_modules()
    modules[PACKAGE_NAME] = importlib.import_module(PACKAGE_ROOT)  # type: ignore

    return modules


def main() -> None:
    """
    Shim the dbt CLI to include our custom modules.

    - https://docs.getdbt.com/reference/programmatic-invocations
    """
    dbt.context.base.get_context_modules = new_get_context_modules
    dbt.cli.main.dbtRunner().invoke(sys.argv[1:])
