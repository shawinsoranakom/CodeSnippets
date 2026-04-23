def _generate_and_validate_mypy_config(config: Config) -> str:
    """Validate and generate mypy config."""

    # Filter empty and commented lines.
    parsed_modules: list[str] = [
        line.strip()
        for line in config.cache["strict_typing"].splitlines()
        if line.strip() != "" and not line.startswith("#")
    ]

    strict_modules: list[str] = []
    strict_core_modules: list[str] = []
    for module in parsed_modules:
        if module.startswith("homeassistant.components"):
            strict_modules.append(module)
        else:
            strict_core_modules.append(module)

    # Validate that all modules exist.
    all_modules = (
        strict_modules + strict_core_modules + list(NO_IMPLICIT_REEXPORT_MODULES)
    )
    for module in all_modules:
        if module.endswith(".*"):
            module_path = Path(module[:-2].replace(".", os.path.sep))
            if not module_path.is_dir():
                config.add_error("mypy_config", f"Module '{module} is not a folder")
        else:
            module = module.replace(".", os.path.sep)
            module_path = Path(f"{module}.py")
            if module_path.is_file():
                continue
            module_path = Path(module) / "__init__.py"
            if not module_path.is_file():
                config.add_error("mypy_config", f"Module '{module} doesn't exist")

    # Don't generate mypy.ini if there're errors found because it will likely crash.
    if any(err.plugin == "mypy_config" for err in config.errors):
        return ""

    mypy_config = configparser.ConfigParser()

    general_section = "mypy"
    mypy_config.add_section(general_section)
    for key, value in GENERAL_SETTINGS.items():
        mypy_config.set(general_section, key, value)
    for key in STRICT_SETTINGS:
        mypy_config.set(general_section, key, "true")

    for plugin_name, plugin_config in PLUGIN_CONFIG.items():
        if not plugin_config:
            continue
        mypy_config.add_section(plugin_name)
        for key, value in plugin_config.items():
            mypy_config.set(plugin_name, key, value)

    # By default enable no_implicit_reexport only for homeassistant.*
    # Disable it afterwards for all components
    components_section = "mypy-homeassistant.*"
    mypy_config.add_section(components_section)
    mypy_config.set(components_section, "no_implicit_reexport", "true")

    for core_module in strict_core_modules:
        core_section = f"mypy-{core_module}"
        mypy_config.add_section(core_section)
        for key in STRICT_SETTINGS_CORE:
            mypy_config.set(core_section, key, "true")

    # By default strict checks are disabled for components.
    components_section = "mypy-homeassistant.components.*"
    mypy_config.add_section(components_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(components_section, key, "false")
    mypy_config.set(components_section, "no_implicit_reexport", "false")

    for strict_module in strict_modules:
        strict_section = f"mypy-{strict_module}"
        mypy_config.add_section(strict_section)
        for key in STRICT_SETTINGS:
            mypy_config.set(strict_section, key, "true")
        if strict_module in NO_IMPLICIT_REEXPORT_MODULES:
            mypy_config.set(strict_section, "no_implicit_reexport", "true")

    for reexport_module in sorted(
        NO_IMPLICIT_REEXPORT_MODULES.difference(strict_modules)
    ):
        reexport_section = f"mypy-{reexport_module}"
        mypy_config.add_section(reexport_section)
        mypy_config.set(reexport_section, "no_implicit_reexport", "true")

    # Disable strict checks for tests
    tests_section = "mypy-tests.*"
    mypy_config.add_section(tests_section)
    for key in STRICT_SETTINGS:
        mypy_config.set(tests_section, key, "false")

    with io.StringIO() as fp:
        mypy_config.write(fp)
        fp.seek(0)
        return f"{HEADER}{fp.read().strip()}\n"