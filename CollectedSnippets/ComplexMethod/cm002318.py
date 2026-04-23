def check_public_method_exists(documented_methods_map):
    """Check that all explicitly documented public methods are defined in the corresponding class."""
    failures = []
    for obj, methods in documented_methods_map.items():
        # Let's ensure there is no repetition
        if len(set(methods)) != len(methods):
            failures.append(f"Error in the documentation of {obj}: there are repeated documented methods.")

        # Navigates into the object, given the full import path
        nested_path = obj.split(".")
        submodule = transformers
        if len(nested_path) > 1:
            nested_submodules = nested_path[:-1]
            for submodule_name in nested_submodules:
                if submodule_name == "transformers":
                    continue

                try:
                    submodule = getattr(submodule, submodule_name)
                except AttributeError:
                    failures.append(f"Could not parse {submodule_name}. Are the required dependencies installed?")
                continue

        class_name = nested_path[-1]

        try:
            obj_class = getattr(submodule, class_name)
        except AttributeError:
            failures.append(f"Could not parse {class_name}. Are the required dependencies installed?")
            continue

        # Checks that all explicitly documented methods are defined in the class
        for method in methods:
            if method == "all":  # Special keyword to document all public methods
                continue
            try:
                if not hasattr(obj_class, method):
                    failures.append(
                        "The following public method is explicitly documented but not defined in the corresponding "
                        f"class. class: {obj}, method: {method}. If the method is defined, this error can be due to "
                        f"lacking dependencies."
                    )
            except ImportError:
                pass

    if len(failures) > 0:
        raise Exception("\n".join(failures))