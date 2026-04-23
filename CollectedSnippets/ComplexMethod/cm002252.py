def convert_relative_import_to_absolute(
    import_node: cst.ImportFrom,
    file_path: str,
    package_name: str | None = "transformers",
) -> cst.ImportFrom:
    """
    Convert a relative libcst.ImportFrom node into an absolute one,
    using the file path and package name.

    Args:
        import_node: A relative import node (e.g. `from ..utils import helper`)
        file_path: Path to the file containing the import (can be absolute or relative)
        package_name: The top-level package name (e.g. 'myproject')

    Returns:
        A new ImportFrom node with the absolute import path
    """
    if not (import_node.relative and len(import_node.relative) > 0):
        return import_node  # Already absolute

    file_path = os.path.abspath(file_path)
    rel_level = len(import_node.relative)

    # Strip file extension and split into parts
    file_path_no_ext = file_path.removesuffix(".py")
    file_parts = file_path_no_ext.split(os.path.sep)

    # Ensure the file path includes the package name
    if package_name not in file_parts:
        raise ValueError(f"Package name '{package_name}' not found in file path '{file_path}'")

    # Slice file_parts starting from the package name
    pkg_index = file_parts.index(package_name)
    module_parts = file_parts[pkg_index + 1 :]  # e.g. ['module', 'submodule', 'foo']
    if len(module_parts) < rel_level:
        raise ValueError(f"Relative import level ({rel_level}) goes beyond package root.")

    base_parts = module_parts[:-rel_level]

    # Flatten the module being imported (if any)
    def flatten_module(module: cst.BaseExpression | None) -> list[str]:
        if not module:
            return []
        if isinstance(module, cst.Name):
            return [module.value]
        elif isinstance(module, cst.Attribute):
            parts = []
            while isinstance(module, cst.Attribute):
                parts.insert(0, module.attr.value)
                module = module.value
            if isinstance(module, cst.Name):
                parts.insert(0, module.value)
            return parts
        return []

    import_parts = flatten_module(import_node.module)

    # Combine to get the full absolute import path
    full_parts = [package_name] + base_parts + import_parts

    # Handle special case where the import comes from a namespace package (e.g. optimum with `optimum.habana`, `optimum.intel` instead of `src.optimum`)
    if package_name != "transformers" and file_parts[pkg_index - 1] != "src":
        full_parts = [file_parts[pkg_index - 1]] + full_parts

    # Build the dotted module path
    dotted_module: cst.BaseExpression | None = None
    for part in full_parts:
        name = cst.Name(part)
        dotted_module = name if dotted_module is None else cst.Attribute(value=dotted_module, attr=name)

    # Return a new ImportFrom node with absolute import
    return import_node.with_changes(module=dotted_module, relative=[])