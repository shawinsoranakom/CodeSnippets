def build(cls, path: str) -> str:
        """Build the import definition."""
        hint_type_list = cls.get_path_hint_type_list(path=path)
        code = "from openbb_core.app.static.container import Container"
        code += "\nfrom openbb_core.app.model.obbject import OBBject"

        # These imports were not detected before build, so we add them manually and
        # ruff --fix the resulting code to remove unused imports.
        # TODO: Find a better way to handle this. This is a temporary solution.
        code += "\nimport openbb_core.provider"
        code += "\nfrom openbb_core.provider.abstract.data import Data"
        code += "\nimport pandas"
        code += "\nfrom pandas import DataFrame, Series"
        code += "\nimport numpy"
        code += "\nfrom numpy import ndarray"
        code += "\nimport datetime"
        code += "\nfrom datetime import date"
        code += "\nimport pydantic"
        code += "\nfrom pydantic import BaseModel"
        code += "\nfrom inspect import Parameter"
        code += "\nimport typing"
        code += "\nfrom typing import TYPE_CHECKING, Annotated, ForwardRef, Union, Optional, Literal, Any"
        code += "\nfrom annotated_types import Ge, Le, Gt, Lt"
        code += "\nfrom warnings import warn, simplefilter"
        code += "\nfrom openbb_core.app.static.utils.decorators import exception_handler, validate\n"
        code += "\nfrom openbb_core.app.static.utils.filters import filter_inputs\n"
        code += "\nfrom openbb_core.app.deprecation import OpenBBDeprecationWarning\n"
        code += "\nfrom openbb_core.app.model.field import OpenBBField"
        code += "\nfrom fastapi import Depends"

        module_list = [
            hint_type.__module__
            for hint_type in hint_type_list
            if hasattr(hint_type, "__module__")
        ]
        module_list = list(set(module_list))
        module_list.sort()  # type: ignore

        code += "\n"
        for module in module_list:
            code += f"import {module}\n"

        # Group types by module and capture the return types for the imports.
        module_types: dict = {}
        for hint_type in hint_type_list:
            if hasattr(hint_type, "__module__") and hint_type.__module__ != "builtins":
                module = hint_type.__module__

                if hasattr(hint_type, "__origin__"):
                    type_name = (
                        hint_type.__origin__.__name__
                        if hasattr(hint_type.__origin__, "__name__")
                        else str(hint_type.__origin__)
                    )
                else:
                    raw_type_name = getattr(
                        hint_type,
                        "__name__",
                        str(hint_type).rsplit(".", maxsplit=1)[-1],
                    )
                    type_name = (
                        raw_type_name.split("[")[0]
                        if "[" in raw_type_name
                        else raw_type_name
                    )

                type_name_str = str(type_name)
                if type_name_str.startswith("typing.Optional"):
                    continue
                if "|" in type_name_str:
                    continue

                sanitized_name = cls._sanitize_type_name(type_name_str)
                if not sanitized_name:
                    continue
                if (
                    module == "typing" and sanitized_name in dir(__builtins__)
                ) or sanitized_name in {
                    "Dict",
                    "List",
                    "int",
                    "float",
                    "str",
                    "dict",
                    "list",
                    "set",
                    "bool",
                    "tuple",
                }:
                    continue
                if not (
                    sanitized_name == "TYPE_CHECKING" or sanitized_name.isidentifier()
                ):
                    continue

                if module not in module_types:
                    module_types[module] = set()

                module_types[module].add(sanitized_name)

        # Generate from-import statements for modules with specific types
        for module, types in sorted(module_types.items()):
            if module == "types":
                continue
            _types = types
            if module == "typing":
                _types = {t for t in types if hasattr(typing_module, t)}
                if not _types:
                    continue

            if len(_types) == 1:
                type_name = next(iter(_types))
                code += f"\nfrom {module} import {type_name}"
            else:
                import_types = [
                    d
                    for d in sorted(_types)
                    if d
                    not in [
                        "Dict",
                        "List",
                        "int",
                        "float",
                        "str",
                        "dict",
                        "list",
                        "set",
                    ]
                ]
                if import_types:
                    code += f"\nfrom {module} import ("
                    for type_name in import_types:
                        code += f"\n    {type_name},"
                    code += "\n)"
                    code += "\n"

        return code + "\n"