def get_provider_param_mapping(provider: str) -> dict[str, str]:
    """Get parameter mapping for a provider.

    Builds the mapping from the provider's variables using their langchain_param values.
    Returns dict with keys like: model_class, model_param, and dynamically built param mappings.

    Args:
        provider: The provider name (e.g., "OpenAI", "Anthropic", "IBM WatsonX")

    Returns:
        Dict containing parameter mappings for the provider.
        Returns empty dict if provider is not found.
    """
    metadata = MODEL_PROVIDER_METADATA.get(provider, {})
    if not metadata:
        return {}

    # Start with the base mapping (model_class, model_param)
    result = dict(metadata.get("mapping", {}))

    # Build param mappings from variables using component_metadata.mapping_field
    for var in metadata.get("variables", []):
        component_meta = var.get("component_metadata", {})
        mapping_field = component_meta.get("mapping_field")
        langchain_param = var.get("langchain_param")

        if mapping_field and langchain_param:
            # Create the param key based on the mapping_field type
            if "api_key" in mapping_field:
                result["api_key_param"] = langchain_param
            elif "url" in mapping_field.lower() or "base_url" in mapping_field.lower():
                # Distinguish between different URL types
                if "ollama" in mapping_field.lower():
                    result["base_url_param"] = langchain_param
                elif "watsonx" in mapping_field.lower() or provider == "IBM WatsonX":
                    result["url_param"] = langchain_param
                else:
                    result["base_url_param"] = langchain_param
            elif "project_id" in mapping_field:
                result["project_id_param"] = langchain_param

    return result