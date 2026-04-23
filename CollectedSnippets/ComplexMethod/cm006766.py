def get_unified_models_detailed(
    providers: list[str] | None = None,
    model_name: str | None = None,
    model_type: str | None = None,
    *,
    include_unsupported: bool | None = None,
    include_deprecated: bool | None = None,
    only_defaults: bool = False,
    **metadata_filters,
):
    """Return a list of providers and their models, optionally filtered.

    Parameters
    ----------
    providers : list[str] | None
        If given, only models from these providers are returned.
    model_name : str | None
        If given, only the model with this exact name is returned.
    model_type : str | None
        Optional. Restrict to models whose metadata "model_type" matches this value.
    include_unsupported : bool
        When False (default) models whose metadata contains ``not_supported=True``
        are filtered out.
    include_deprecated : bool
        When False (default) models whose metadata contains ``deprecated=True``
        are filtered out.
    only_defaults : bool
        When True, only models marked as default are returned.
        The first 5 models from each provider (in list order) are automatically
        marked as default. Defaults to False to maintain backward compatibility.
    **metadata_filters
        Arbitrary key/value pairs to match against the model's metadata.
        Example: ``get_unified_models_detailed(size="4k", context_window=8192)``
    """
    if include_unsupported is None:
        include_unsupported = False
    if include_deprecated is None:
        include_deprecated = False

    # Gather all models from imported *_MODELS_DETAILED lists
    all_models: list[dict] = []
    for models_detailed in MODELS_DETAILED:
        all_models.extend(models_detailed)

    # Apply filters
    filtered_models: list[dict] = []
    for md in all_models:
        # Skip models flagged as not_supported unless explicitly included
        if (not include_unsupported) and md.get("not_supported", False):
            continue

        # Skip models flagged as deprecated unless explicitly included
        if (not include_deprecated) and md.get("deprecated", False):
            continue

        if providers and md.get("provider") not in providers:
            continue
        if model_name and md.get("name") != model_name:
            continue
        if model_type and md.get("model_type") != model_type:
            continue
        # Match arbitrary metadata key/value pairs
        if any(md.get(k) != v for k, v in metadata_filters.items()):
            continue

        filtered_models.append(md)

    # Group by provider
    provider_map: dict[str, list[dict]] = {}
    for metadata in filtered_models:
        prov = metadata.get("provider", "Unknown")
        provider_map.setdefault(prov, []).append(
            {
                "model_name": metadata.get("name"),
                "metadata": {k: v for k, v in metadata.items() if k not in ("provider", "name")},
            }
        )

    # Mark the first 5 models in each provider as default (based on list order)
    # and optionally filter to only defaults
    default_model_count = 5  # Number of default models per provider

    for prov, models in provider_map.items():
        for i, model in enumerate(models):
            if i < default_model_count:
                model["metadata"]["default"] = True
            else:
                model["metadata"]["default"] = False

        # If only_defaults is True, filter to only default models
        if only_defaults:
            provider_map[prov] = [m for m in models if m["metadata"].get("default", False)]

    # Format as requested
    return [
        {
            "provider": prov,
            "models": models,
            "num_models": len(models),
            **model_provider_metadata.get(prov, {}),
        }
        for prov, models in provider_map.items()
    ]