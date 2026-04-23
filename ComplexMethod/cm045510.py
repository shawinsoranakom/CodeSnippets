def get_module_hierarchy(package_root: Path) -> Dict[str, Set[str]]:
    """Get the module hierarchy for a package, filtering only documented packages."""
    modules: Dict[str, Set[str]] = {}

    for root, dirs, files in os.walk(package_root):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__') and not d.startswith('.')]

        root_path = Path(root)

        # Process Python files (excluding private modules)
        for file in files:
            if file.endswith('.py') and file != '__init__.py' and not file.startswith('_'):
                file_path = root_path / file
                module_path = file_path.relative_to(package_root)

                # Convert file path to module name
                module_parts = list(module_path.parts[:-1]) + [module_path.stem]

                if module_parts:
                    # Skip if any part of the module path is private
                    if is_private_module(module_parts):
                        continue

                    module_name = '.'.join(module_parts)
                    package_name = module_parts[0]

                    # Only include modules from documented packages
                    if package_name in DOCUMENTED_PACKAGES:
                        if package_name not in modules:
                            modules[package_name] = set()

                        modules[package_name].add(module_name)

        # Also check for directories with __init__.py (packages, excluding private)
        for dir_name in dirs:
            if not dir_name.startswith('_'):  # Skip private directories
                dir_path = root_path / dir_name
                if (dir_path / '__init__.py').exists():
                    module_path = dir_path.relative_to(package_root)
                    module_parts = list(module_path.parts)

                    if module_parts:
                        # Skip if any part of the module path is private
                        if is_private_module(module_parts):
                            continue

                        module_name = '.'.join(module_parts)
                        package_name = module_parts[0]

                        # Only include modules from documented packages
                        if package_name in DOCUMENTED_PACKAGES:
                            if package_name not in modules:
                                modules[package_name] = set()

                            modules[package_name].add(module_name)

    return modules