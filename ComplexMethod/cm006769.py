def normalize_model_names_to_dicts(
    model_names: list[str] | str,
) -> list[dict[str, Any]]:
    """Convert simple model name(s) to list of dicts format."""
    # Convert single string to list
    if isinstance(model_names, str):
        model_names = [model_names]

    # Get all available models to look up metadata
    try:
        all_models = get_unified_models_detailed()
    except Exception:  # noqa: BLE001
        # If we can't get models, just create basic dicts
        return [{"name": name} for name in model_names]

    # Build a lookup map of model_name -> full model data with runtime metadata
    model_lookup = {}
    for provider_data in all_models:
        provider = provider_data.get("provider")
        icon = provider_data.get("icon", "Bot")
        for model_data in provider_data.get("models", []):
            model_name = model_data.get("model_name")
            base_metadata = model_data.get("metadata", {})

            # Get parameter mapping for this provider
            param_mapping = get_provider_param_mapping(provider)

            # Build runtime metadata similar to get_language_model_options
            runtime_metadata = {
                "context_length": 128000,  # Default
                "model_class": param_mapping.get("model_class", "ChatOpenAI"),
                "model_name_param": param_mapping.get("model_param", "model"),
                "api_key_param": param_mapping.get("api_key_param", "api_key"),
            }

            # Add max_tokens_field_name from provider metadata
            provider_meta = model_provider_metadata.get(provider, {})
            if "max_tokens_field_name" in provider_meta:
                runtime_metadata["max_tokens_field_name"] = provider_meta["max_tokens_field_name"]

            # Add reasoning models list for OpenAI
            if provider == "OpenAI" and base_metadata.get("reasoning"):
                runtime_metadata["reasoning_models"] = [model_name]

            # Add provider-specific params from mapping
            if "base_url_param" in param_mapping:
                runtime_metadata["base_url_param"] = param_mapping["base_url_param"]
            if "url_param" in param_mapping:
                runtime_metadata["url_param"] = param_mapping["url_param"]
            if "project_id_param" in param_mapping:
                runtime_metadata["project_id_param"] = param_mapping["project_id_param"]

            # Merge base metadata with runtime metadata
            full_metadata = {**base_metadata, **runtime_metadata}

            model_lookup[model_name] = {
                "name": model_name,
                "icon": icon,
                "category": provider,
                "provider": provider,
                "metadata": full_metadata,
            }

    # Convert string list to dict list
    result = []
    for name in model_names:
        if name in model_lookup:
            result.append(model_lookup[name])
        else:
            # Model not found in registry, create basic entry with minimal required metadata
            result.append(
                {
                    "name": name,
                    "provider": "Unknown",
                    "metadata": {
                        "model_class": "ChatOpenAI",  # Default fallback
                        "model_name_param": "model",
                        "api_key_param": "api_key",
                    },
                }
            )

    return result