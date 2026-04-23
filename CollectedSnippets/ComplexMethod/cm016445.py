def _generate_imports(
        cls, async_class: type, type_tracker: TypeTracker
    ) -> list[str]:
        """Generate import statements for the stub file."""
        imports = []

        # Add standard typing imports
        imports.append(
            "from typing import Any, Dict, List, Optional, Tuple, Union, Set, Sequence, cast, NamedTuple"
        )

        # Add imports from the original module
        if async_class.__module__ != "builtins":
            module = inspect.getmodule(async_class)
            additional_types = []

            if module:
                # Check if module has __all__ defined
                module_all = getattr(module, "__all__", None)

                for name, obj in sorted(inspect.getmembers(module)):
                    if isinstance(obj, type):
                        # Skip if __all__ is defined and this name isn't in it
                        # unless it's already been tracked as used in type annotations
                        if module_all is not None and name not in module_all:
                            # Check if this type was actually used in annotations
                            if name not in type_tracker.discovered_types:
                                continue

                        # Check for NamedTuple
                        if issubclass(obj, tuple) and hasattr(obj, "_fields"):
                            additional_types.append(name)
                            # Mark as already imported
                            type_tracker.already_imported.add(name)
                        # Check for Enum
                        elif issubclass(obj, Enum) and name != "Enum":
                            additional_types.append(name)
                            # Mark as already imported
                            type_tracker.already_imported.add(name)

            if additional_types:
                type_imports = ", ".join([async_class.__name__] + additional_types)
                imports.append(f"from {async_class.__module__} import {type_imports}")
            else:
                imports.append(
                    f"from {async_class.__module__} import {async_class.__name__}"
                )

        # Add imports for all discovered types
        # Pass the main module name to avoid duplicate imports
        imports.extend(
            type_tracker.get_imports(main_module_name=async_class.__module__)
        )

        # Add base module import if needed
        if hasattr(inspect.getmodule(async_class), "__name__"):
            module_name = inspect.getmodule(async_class).__name__
            if "." in module_name:
                base_module = module_name.split(".")[0]
                # Only add if not already importing from it
                if not any(imp.startswith(f"from {base_module}") for imp in imports):
                    imports.append(f"import {base_module}")

        return imports