def _resolve_embedding_provider_packages(provider_name: str) -> set[str]:
    """Resolve PyPI packages needed for an embedding model provider.

    The ``EmbeddingModelComponent`` follows the same dynamic-import pattern as
    the ``LanguageModelComponent``: its code field only imports from ``lfx``
    internals, while the actual provider package (e.g. ``langchain-openai``) is
    imported at runtime via ``get_embedding_class()``.

    This function bridges that gap by chaining two registries from
    ``unified_models.py``:

    1. ``EMBEDDING_PROVIDER_CLASS_MAPPING``: provider name → embedding class name
    2. ``_EMBEDDING_CLASS_IMPORTS``: class name → (module_path, attr, install_hint)

    Because both registries live in ``unified_models.py``, adding a new
    embedding provider there automatically makes it visible here — no
    separate mapping to maintain.
    """
    try:
        from lfx.base.models.unified_models import (
            _EMBEDDING_CLASS_IMPORTS,
            EMBEDDING_PROVIDER_CLASS_MAPPING,
        )
    except ImportError:
        warnings.warn(
            "Could not import embedding registries from unified_models. "
            f"Embedding packages for provider '{provider_name}' will not be resolved.",
            stacklevel=2,
        )
        return set()

    class_name = EMBEDDING_PROVIDER_CLASS_MAPPING.get(provider_name)
    if not class_name:
        # This provider has no embedding support (e.g. Anthropic, Groq).
        # This is expected — not a warning — since this function is called
        # for every detected provider, including language-model-only ones.
        return set()

    import_info = _EMBEDDING_CLASS_IMPORTS.get(class_name)
    if not import_info:
        warnings.warn(
            f"Embedding class '{class_name}' for provider '{provider_name}' is in "
            "EMBEDDING_PROVIDER_CLASS_MAPPING but not in _EMBEDDING_CLASS_IMPORTS. "
            "The import registry in unified_models.py may need updating.",
            stacklevel=2,
        )
        return set()

    module_path, _attr_name, install_hint = import_info

    # Use install_hint if provided (handles internal module paths like lfx.base.models.*)
    if install_hint:
        return {install_hint}

    top_level = module_path.split(".")[0]
    if top_level in STDLIB_MODULES or top_level in _INTERNAL_IMPORT_NAMES:
        return set()

    lfx_provided = _get_lfx_provided_imports()
    if top_level in lfx_provided:
        return set()

    return {_import_to_package(top_level)}