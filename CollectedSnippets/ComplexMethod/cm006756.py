def process_inputs(component_data: Input, provider_name: str | None = None):
    """Processes and modifies an input configuration based on its type or name.

    Adjusts properties such as value, advanced status, real-time refresh, and additional information for specific
    input types or names to ensure correct behavior in the UI and provider integration.

    Args:
        component_data: The input configuration to process.
        provider_name: The name of the provider to process the inputs for.

    Returns:
        The modified input configuration.
    """
    if isinstance(component_data, SecretStrInput):
        component_data.value = ""
        component_data.load_from_db = False
        component_data.real_time_refresh = True
        if component_data.name == "api_key":
            component_data.required = False
    elif component_data.name == "tool_model_enabled":
        component_data.advanced = True
        component_data.value = True
    elif component_data.name in {"temperature", "base_url"}:
        if provider_name not in ["IBM watsonx.ai", "Ollama"]:
            component_data = set_advanced_true(component_data)
    elif component_data.name == "model_name":
        if provider_name not in ["IBM watsonx.ai"]:
            component_data = set_real_time_refresh_false(component_data)
        component_data = add_combobox_true(component_data)
        component_data = add_info(
            component_data,
            "To see the model names, first choose a provider. Then, enter your API key and click the refresh button "
            "next to the model name.",
        )
    return component_data