def _extract_component_requirements(node: dict) -> tuple[set[str], set[str]]:
    """Extract requirements from a single flow node.

    Returns:
        A tuple of (package_names, provider_names) where package_names are
        PyPI packages required by the component code and provider_names are
        model provider strings detected from the template configuration.
    """
    packages: set[str] = set()

    node_data = node.get("data", {})
    node_info = node_data.get("node", {})
    template = node_info.get("template", {})

    lfx_provided = _get_lfx_provided_imports()

    # --- 1. Static analysis: parse the component code ---
    code_field = template.get("code")
    if isinstance(code_field, dict):
        source = code_field.get("value")
        if source and isinstance(source, str):
            imports = _extract_imports(source)
            for imp in imports:
                # Skip stdlib
                if imp in STDLIB_MODULES:
                    continue
                # Skip lfx / langflow internal imports - lfx provides these
                # interfaces at runtime so they should never be listed as
                # separate requirements.
                if imp in _INTERNAL_IMPORT_NAMES:
                    continue

                # Always check extra runtime deps (e.g. bs4 → lxml, tabulate)
                # even if the import itself is provided by lfx, because the
                # extras may not be.
                if imp in MODULE_EXTRA_DEPS:
                    for extra in MODULE_EXTRA_DEPS[imp]:
                        packages.add(extra)

                # Skip imports already provided by lfx
                if imp in lfx_provided:
                    continue

                pkg = _import_to_package(imp)
                packages.add(pkg)

    # --- 2. Dynamic analysis: detect provider from template fields ---
    providers = _detect_providers_from_template(template)

    return packages, providers