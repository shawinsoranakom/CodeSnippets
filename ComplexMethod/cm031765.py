def list_modules() -> set[str]:
    names: set[str] = set()

    list_builtin_modules(names)
    list_modules_setup_extensions(names)
    list_packages(names)
    list_python_modules(names)
    list_frozen(names)

    # Remove ignored packages and modules
    for name in list(names):
        package_name = name.split('.')[0]
        # package_name can be equal to name
        if package_name in IGNORE:
            names.discard(name)

    # Sanity checks
    for name in names:
        if "." in name:
            raise Exception(f"sub-modules must not be listed: {name}")
        if ("test" in name or "xx" in name) and name not in ALLOW_TEST_MODULES:
            raise Exception(f"test modules must not be listed: {name}")

    return names