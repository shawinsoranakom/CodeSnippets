def replace_with_live_models(
    provider_models: list[dict],
    user_id: UUID | str | None,
    enabled_providers: set[str] | list[str],
    model_type: str | None = None,
    provider_metadata: dict | None = None,
) -> list[dict]:
    """Replace static model entries with live models for providers in LIVE_MODEL_PROVIDERS.

    Iterates over LIVE_MODEL_PROVIDERS; for each that is in *enabled_providers*,
    fetches live models via get_live_models_for_provider and replaces (or appends)
    the provider entry in *provider_models*.

    Args:
        provider_models: List of provider dicts (same shape as get_unified_models_detailed output).
        user_id: Current user ID for credential lookup.
        enabled_providers: Set/list of provider names that are currently enabled/configured.
        model_type: ``"llm"``, ``"embeddings"``, or ``None`` (fetch both and concatenate).
        provider_metadata: Optional dict of extra provider metadata to merge into the entry.

    Returns:
        The (possibly modified) provider_models list.
    """
    if not user_id or not enabled_providers:
        return provider_models

    for provider in LIVE_MODEL_PROVIDERS:
        if provider not in enabled_providers:
            continue

        if model_type is None:
            live_llm = get_live_models_for_provider(user_id, provider, "llm")
            live_emb = get_live_models_for_provider(user_id, provider, "embeddings")
            live_models = live_llm + live_emb
        else:
            live_models = get_live_models_for_provider(user_id, provider, model_type)

        catalog_models = _live_models_to_catalog_shape(live_models) if live_models else []

        # Try to find and replace existing provider entry
        replaced = False
        for provider_dict in provider_models:
            if provider_dict.get("provider") == provider:
                provider_dict["models"] = catalog_models
                provider_dict["num_models"] = len(catalog_models)
                replaced = True
                break

        if not replaced and catalog_models:
            entry: dict = {
                "provider": provider,
                "models": catalog_models,
                "num_models": len(catalog_models),
            }
            if provider_metadata and provider in provider_metadata:
                entry.update(provider_metadata[provider])
            provider_models.append(entry)

    return provider_models