def convert_to_relative_import(import_node: cst.ImportFrom, file_path: str, package_name: str) -> cst.ImportFrom:
    """
    Convert an absolute import to a relative one if it belongs to `package_name`.

    Parameters:
    - node: The ImportFrom node to possibly transform.
    - file_path: Absolute path to the file containing the import (e.g., '/path/to/mypackage/foo/bar.py').
    - package_name: The top-level package name (e.g., 'mypackage').

    Returns:
    - A possibly modified ImportFrom node.
    """
    if import_node.relative:
        return import_node  # Already relative import

    # Extract module name string from ImportFrom
    def get_module_name(module):
        if isinstance(module, cst.Name):
            return module.value, [module.value]
        elif isinstance(module, cst.Attribute):
            parts = []
            while isinstance(module, cst.Attribute):
                parts.append(module.attr.value)
                module = module.value
            if isinstance(module, cst.Name):
                parts.append(module.value)
            parts.reverse()
            return ".".join(parts), parts
        return "", None

    module_name, submodule_list = get_module_name(import_node.module)

    # Check if it's from the target package
    if (
        not (module_name.startswith(package_name + ".") or module_name.startswith("optimum." + package_name + "."))
        and module_name != package_name
    ):
        return import_node  # Not from target package

    # Locate the package root inside the file path
    norm_file_path = os.path.normpath(file_path)
    parts = norm_file_path.split(os.sep)

    try:
        pkg_index = parts.index(package_name)
    except ValueError:
        # Package name not found in path — assume we can't resolve relative depth
        return import_node

    # Depth is how many directories after the package name before the current file
    depth = len(parts) - pkg_index - 1  # exclude the .py file itself
    for i, submodule in enumerate(parts[pkg_index + 1 :]):
        if submodule == submodule_list[2 + i]:
            depth -= 1
        else:
            break

    # Create the correct number of dots
    relative = [cst.Dot()] * depth if depth > 0 else [cst.Dot()]

    # Strip package prefix from import module path
    if module_name.startswith("optimum." + package_name + "."):
        stripped_name = module_name[len("optimum." + package_name) :].lstrip(".")
    else:
        stripped_name = module_name[len(package_name) :].lstrip(".")

    # Build new module node
    if stripped_name == "":
        new_module = None
    else:
        name_parts = stripped_name.split(".")[i:]
        new_module = cst.Name(name_parts[0])
        for part in name_parts[1:]:
            new_module = cst.Attribute(value=new_module, attr=cst.Name(part))

    return import_node.with_changes(module=new_module, relative=relative)