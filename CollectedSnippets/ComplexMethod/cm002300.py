def get_module_dependencies(module_fname: str, cache: dict[str, list[str]] | None = None) -> list[str]:
    """
    Refines the result of `extract_imports` to remove subfolders and get a proper list of module filenames: if a file
    as an import `from utils import Foo, Bar`, with `utils` being a subfolder containing many files, this will traverse
    the `utils` init file to check where those dependencies come from: for instance the files utils/foo.py and utils/bar.py.

    Warning: This presupposes that all intermediate inits are properly built (with imports from the respective
    submodules) and work better if objects are defined in submodules and not the intermediate init (otherwise the
    intermediate init is added, and inits usually have a lot of dependencies).

    Args:
        module_fname (`str`):
            The name of the file of the module where we want to look at the imports (given relative to the root of
            the repo).
        cache (Dictionary `str` to `List[str]`, *optional*):
            To speed up this function if it was previously called on `module_fname`, the cache of all previously
            computed results.

    Returns:
        `List[str]`: The list of module filenames imported in the input `module_fname` (with submodule imports refined).
    """
    dependencies = []
    imported_modules = extract_imports(module_fname, cache=cache)
    # The while loop is to recursively traverse all inits we may encounter: we will add things as we go.
    while len(imported_modules) > 0:
        new_modules = []
        for module, imports in imported_modules:
            if "models" in module.split("/") and module.split("/")[-1].startswith("convert_"):
                continue
            # If we end up in an __init__ we are often not actually importing from this init (except in the case where
            # the object is fully defined in the __init__)
            if module.endswith("__init__.py"):
                # So we get the imports from that init then try to find where our objects come from.
                new_imported_modules = dict(extract_imports(module, cache=cache))

                # Add imports via `define_import_structure` after the #35167 as we remove explicit import in `__init__.py`
                from transformers.utils.import_utils import define_import_structure

                new_imported_modules_from_import_structure = define_import_structure(PATH_TO_REPO / module)

                for mapping in new_imported_modules_from_import_structure.values():
                    for _module, _imports in mapping.items():
                        # Import Structure returns _module keys as import paths rather than local paths
                        # We replace with os.path.sep so that it's Windows-compatible
                        _module = _module.replace(".", os.path.sep)
                        _module = module.replace("__init__.py", f"{_module}.py")
                        if _module not in new_imported_modules:
                            new_imported_modules[_module] = list(_imports)
                        else:
                            original_imports = new_imported_modules[_module]
                            for potential_new_item in list(_imports):
                                if potential_new_item not in original_imports:
                                    new_imported_modules[_module].append(potential_new_item)

                for new_module, new_imports in new_imported_modules.items():
                    if any(i in new_imports for i in imports):
                        if new_module not in dependencies:
                            new_modules.append((new_module, [i for i in new_imports if i in imports]))
                        imports = [i for i in imports if i not in new_imports]

                if len(imports) > 0:
                    # If there are any objects lefts, they may be a submodule
                    path_to_module = PATH_TO_REPO / module.replace("__init__.py", "")
                    dependencies.extend(
                        [
                            os.path.join(module.replace("__init__.py", ""), f"{i}.py")
                            for i in imports
                            if (path_to_module / f"{i}.py").is_file()
                        ]
                    )
                    imports = [i for i in imports if not (path_to_module / f"{i}.py").is_file()]
                    if len(imports) > 0:
                        # Then if there are still objects left, they are fully defined in the init, so we keep it as a
                        # dependency.
                        dependencies.append(module)
            else:
                dependencies.append(module)

        imported_modules = new_modules

    return dependencies