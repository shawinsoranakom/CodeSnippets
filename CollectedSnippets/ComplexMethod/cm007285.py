def _resolve_provider_packages(provider_name: str) -> set[str]:
    """Dynamically resolve PyPI packages needed for a model provider.

    Uses ``MODEL_PROVIDERS_DICT`` to look up the provider's component instance,
    then inspects its class's source module to extract import statements.  This
    avoids maintaining a static provider→package mapping table.

    This is specifically necessary because the ``LanguageModelComponent`` delegates
    to provider-specific components (e.g. ``OpenAIModelComponent``) that dynamically
    import the actual model class at runtime.

    Note: only the component's own module is inspected, not parent classes.
    Parent classes (e.g. ``LCModelComponent``) are all part of lfx, so any
    imports they introduce are already in lfx's transitive dependency tree
    and would be filtered out regardless.
    """
    try:
        from lfx.base.models.model_input_constants import MODEL_PROVIDERS_DICT
    except ImportError:
        warnings.warn(
            f"Could not import MODEL_PROVIDERS_DICT. Provider '{provider_name}' packages will not be resolved.",
            stacklevel=2,
        )
        return set()

    provider_info = MODEL_PROVIDERS_DICT.get(provider_name)
    if not provider_info:
        fallback = _PROVIDER_PACKAGE_FALLBACKS.get(provider_name)
        if fallback:
            return set(fallback)
        warnings.warn(
            f"Provider '{provider_name}' was detected in the flow but is not "
            "registered in MODEL_PROVIDERS_DICT (its package may not be installed). "
            "Its dependencies will not be included in requirements.",
            stacklevel=2,
        )
        return set()

    component_instance = provider_info.get("component_class")
    if component_instance is None:
        warnings.warn(
            f"Provider '{provider_name}' has no component instance in MODEL_PROVIDERS_DICT. "
            "Its dependencies will not be included in requirements.",
            stacklevel=2,
        )
        return set()

    try:
        module = inspect.getmodule(type(component_instance))
        if module is None:
            warnings.warn(
                f"Could not locate source module for provider '{provider_name}'. "
                "Its dependencies will not be included in requirements.",
                stacklevel=2,
            )
            return set()
        source = inspect.getsource(module)
    except (OSError, TypeError) as exc:
        warnings.warn(
            f"Could not inspect source for provider '{provider_name}': {exc}. "
            "Its dependencies will not be included in requirements.",
            stacklevel=2,
        )
        return set()

    imports = _extract_imports(source)
    lfx_provided = _get_lfx_provided_imports()
    packages: set[str] = set()
    for imp in imports:
        if imp in STDLIB_MODULES or imp in _INTERNAL_IMPORT_NAMES:
            continue
        if imp in MODULE_EXTRA_DEPS:
            for extra in MODULE_EXTRA_DEPS[imp]:
                packages.add(extra)
        if imp in lfx_provided:
            continue
        packages.add(_import_to_package(imp))
    return packages