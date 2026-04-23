def _find_package_path(import_name: str) -> str:
    """Find the path that contains the package or module."""
    root_mod_name, _, _ = import_name.partition(".")

    try:
        root_spec = importlib.util.find_spec(root_mod_name)

        if root_spec is None:
            raise ValueError("not found")
    except (ImportError, ValueError):
        # ImportError: the machinery told us it does not exist
        # ValueError:
        #    - the module name was invalid
        #    - the module name is __main__
        #    - we raised `ValueError` due to `root_spec` being `None`
        return os.getcwd()

    if root_spec.submodule_search_locations:
        if root_spec.origin is None or root_spec.origin == "namespace":
            # namespace package
            package_spec = importlib.util.find_spec(import_name)

            if package_spec is not None and package_spec.submodule_search_locations:
                # Pick the path in the namespace that contains the submodule.
                package_path = pathlib.Path(
                    os.path.commonpath(package_spec.submodule_search_locations)
                )
                search_location = next(
                    location
                    for location in root_spec.submodule_search_locations
                    if package_path.is_relative_to(location)
                )
            else:
                # Pick the first path.
                search_location = root_spec.submodule_search_locations[0]

            return os.path.dirname(search_location)
        else:
            # package with __init__.py
            return os.path.dirname(os.path.dirname(root_spec.origin))
    else:
        # module
        return os.path.dirname(root_spec.origin)