def get_python_module_utils_imports(compile_targets: list[TestTarget]) -> dict[str, set[str]]:
    """Return a dictionary of module_utils names mapped to sets of python file paths."""
    module_utils = enumerate_module_utils()

    virtual_utils = set(m for m in module_utils if any(m.startswith('%s.' % v) for v in VIRTUAL_PACKAGES))
    module_utils -= virtual_utils

    imports_by_target_path = {}

    for target in compile_targets:
        imports_by_target_path[target.path] = extract_python_module_utils_imports(target.path, module_utils)

    def recurse_import(import_name: str, depth: int = 0, seen: t.Optional[set[str]] = None) -> set[str]:
        """Recursively expand module_utils imports from module_utils files."""
        display.info('module_utils import: %s%s' % ('  ' * depth, import_name), verbosity=4)

        if seen is None:
            seen = {import_name}

        results = {import_name}

        # virtual packages depend on the modules they contain instead of the reverse
        if import_name in VIRTUAL_PACKAGES:
            for sub_import in sorted(virtual_utils):
                if sub_import.startswith('%s.' % import_name):
                    if sub_import in seen:
                        continue

                    seen.add(sub_import)

                    matches = sorted(recurse_import(sub_import, depth + 1, seen))

                    for result in matches:
                        results.add(result)

        import_path = get_import_path(import_name)

        if import_path not in imports_by_target_path:
            import_path = get_import_path(import_name, package=True)

            if import_path not in imports_by_target_path:
                raise ApplicationError('Cannot determine path for module_utils import: %s' % import_name)

        # process imports in reverse so the deepest imports come first
        for name in sorted(imports_by_target_path[import_path], reverse=True):
            if name in virtual_utils:
                continue

            if name in seen:
                continue

            seen.add(name)

            matches = sorted(recurse_import(name, depth + 1, seen))

            for result in matches:
                results.add(result)

        return results

    for module_util in module_utils:
        # recurse over module_utils imports while excluding self
        module_util_imports = recurse_import(module_util)
        module_util_imports.remove(module_util)

        # add recursive imports to all path entries which import this module_util
        for target_path, modules in imports_by_target_path.items():
            if module_util in modules:
                for module_util_import in sorted(module_util_imports):
                    if module_util_import not in modules:
                        display.info('%s inherits import %s via %s' % (target_path, module_util_import, module_util), verbosity=6)
                        modules.add(module_util_import)

    imports: dict[str, set[str]] = {module_util: set() for module_util in module_utils | virtual_utils}

    for target_path, modules in imports_by_target_path.items():
        for module_util in modules:
            imports[module_util].add(target_path)

    # for purposes of mapping module_utils to paths, treat imports of virtual utils the same as the parent package
    for virtual_util in virtual_utils:
        parent_package = '.'.join(virtual_util.split('.')[:-1])
        imports[virtual_util] = imports[parent_package]
        display.info('%s reports imports from parent package %s' % (virtual_util, parent_package), verbosity=6)

    for module_util in sorted(imports):
        if not imports[module_util]:
            package_path = get_import_path(module_util, package=True)

            if os.path.exists(package_path) and not os.path.getsize(package_path):
                continue  # ignore empty __init__.py files

            display.warning('No imports found which use the "%s" module_util.' % module_util)

    return imports