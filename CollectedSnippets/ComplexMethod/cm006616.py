def _discover_all_component_classes() -> list[tuple[str, type]]:
    """Discover all component classes from the lfx.components package.

    Finds all .py files under lfx/components, imports them, and collects
    all classes that inherit from Component.

    Returns:
        List of (fully_qualified_name, class) tuples.
    """
    from lfx.custom.custom_component.component import Component

    discovered: list[tuple[str, type]] = []
    components_pkg_path = Path(lfx.components.__path__[0])
    components_pkg_name = lfx.components.__name__

    # Walk all .py files to discover component modules without relying
    # on pkgutil.walk_packages, which may trigger __init__.py __getattr__
    # and fail on components with missing optional dependencies.
    for root, _dirs, files in os.walk(components_pkg_path):
        for filename in files:
            if not filename.endswith(".py") or filename.startswith("_"):
                continue

            filepath = Path(root) / filename
            # Convert filesystem path to module path
            relative = filepath.relative_to(components_pkg_path)
            parts = list(relative.with_suffix("").parts)
            module_name = f"{components_pkg_name}.{'.'.join(parts)}"

            try:
                module = importlib.import_module(module_name)
            except Exception:  # noqa: S112 - intentionally skip modules with missing optional deps
                continue

            for attr_name, attr_value in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(attr_value, Component)
                    and attr_value is not Component
                    and attr_value.__module__ == module_name
                ):
                    qualified_name = f"{module_name}.{attr_name}"
                    discovered.append((qualified_name, attr_value))

    return discovered