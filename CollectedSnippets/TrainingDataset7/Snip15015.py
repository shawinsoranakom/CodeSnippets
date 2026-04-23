def get_path_and_line(module, fullname):
    path = module_name_to_file_path(module_name=module)

    locator = get_locator(path)

    lineno = locator.node_line_numbers.get(fullname)

    if lineno is not None:
        return path, lineno

    imported_object = fullname.split(".", maxsplit=1)[0]
    try:
        imported_path = locator.import_locations[imported_object]
    except KeyError:
        raise CodeNotFound

    # From a statement such as:
    # from . import y.z
    # - either y.z might be an object in the parent module
    # - or y might be a module, and z be an object in y
    # also:
    # - either the current file is x/__init__.py, and z would be in x.y
    # - or the current file is x/a.py, and z would be in x.a.y
    if path.name != "__init__.py":
        # Look in parent module
        module = module.rsplit(".", maxsplit=1)[0]
    try:
        imported_module = importlib.util.resolve_name(
            name=imported_path, package=module
        )
    except ImportError as error:
        raise ImportError(
            f"Could not import '{imported_path}' in '{module}'."
        ) from error
    try:
        return get_path_and_line(module=imported_module, fullname=fullname)
    except CodeNotFound:
        if "." not in fullname:
            raise

        first_element, remainder = fullname.rsplit(".", maxsplit=1)
        # Retrying, assuming the first element of the fullname is a module.
        return get_path_and_line(
            module=f"{imported_module}.{first_element}", fullname=remainder
        )