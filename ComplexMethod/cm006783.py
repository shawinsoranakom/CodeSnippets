def get_llm(
    model,
    user_id: UUID | str | None,
    api_key=None,
    temperature=None,
    *,
    stream=False,
    max_tokens=None,
    watsonx_url=None,
    watsonx_project_id=None,
    ollama_base_url=None,
) -> Any:
    # Resolve helpers via package namespace so tests patching
    # lfx.base.models.unified_models.<name> keep working.
    from lfx.base.models import unified_models as unified_models_module

    # Coerce provider-specific string params (Message/Data may leak through StrInput)
    ollama_base_url = _to_str(ollama_base_url)
    watsonx_url = _to_str(watsonx_url)
    watsonx_project_id = _to_str(watsonx_project_id)

    # Check if model is already a BaseLanguageModel instance (from a connection)
    try:
        from langchain_core.language_models import BaseLanguageModel

        if isinstance(model, BaseLanguageModel):
            # Model is already instantiated, return it directly
            return model
    except ImportError:
        pass

    # Safely extract model configuration
    if not model or not isinstance(model, list) or len(model) == 0:
        msg = "A model selection is required"
        raise ValueError(msg)

    # Extract the first model (only one expected)
    model = model[0]

    # Extract model configuration from metadata
    model_name = model.get("name")
    provider = model.get("provider")
    metadata = model.get("metadata", {})

    # Get model class and parameter names from metadata
    api_key_param = metadata.get("api_key_param", "api_key")

    # Get API key from user input or global variables
    api_key = unified_models_module.get_api_key_for_provider(user_id, provider, api_key)

    # Validate API key (Ollama doesn't require one)
    if not api_key and provider != "Ollama":
        # Get the correct variable name from the provider variable mapping
        provider_variable_map = unified_models_module.get_model_provider_variable_mapping()
        variable_name = provider_variable_map.get(provider, f"{provider.upper().replace(' ', '_')}_API_KEY")
        msg = (
            f"{provider} API key is required when using {provider} provider. "
            f"Please provide it in the component or configure it globally as {variable_name}."
        )
        raise ValueError(msg)

    # Get model class from metadata, falling back to the provider-level
    # mapping when the stored model value was sourced from
    # ``get_unified_models_detailed`` (which, unlike
    # ``get_language_model_options``, does not inject ``model_class`` into
    # each model's metadata).  This happens for example immediately after a
    # user configures a provider and the frontend augments its dropdown from
    # ``/api/v1/models`` before the backend has repopulated
    # ``template[model]["options"]``; the resulting stored selection only
    # carries the raw ``create_model_metadata`` fields, so we have to derive
    # ``model_class`` from the provider mapping that
    # ``get_language_model_options`` would have used.
    model_class_name = metadata.get("model_class")
    if not model_class_name and provider:
        from lfx.base.models.model_metadata import get_provider_param_mapping

        model_class_name = get_provider_param_mapping(provider).get("model_class")
    if not model_class_name:
        msg = f"No model class defined for {model_name}"
        raise ValueError(msg)
    model_class = unified_models_module.get_model_class(model_class_name)
    model_name_param = metadata.get("model_name_param", "model")

    # Check if this is a reasoning model that doesn't support temperature
    reasoning_models = metadata.get("reasoning_models", [])
    if model_name in reasoning_models:
        temperature = None

    # Build kwargs dynamically
    kwargs = {
        model_name_param: model_name,
        "streaming": stream,
        api_key_param: api_key,
    }

    if temperature is not None:
        kwargs["temperature"] = temperature

    # Add max_tokens with provider-specific field name (only when a valid integer >= 1)
    if max_tokens is not None and max_tokens != "":
        try:
            max_tokens_int = int(max_tokens)
            if max_tokens_int >= 1:
                # Look up provider-specific field name from model metadata first,
                # then fall back to provider metadata, then default to "max_tokens"
                max_tokens_param = metadata.get("max_tokens_field_name")
                if not max_tokens_param:
                    provider_meta = model_provider_metadata.get(provider, {})
                    max_tokens_param = provider_meta.get("max_tokens_field_name", "max_tokens")
                kwargs[max_tokens_param] = max_tokens_int
        except (TypeError, ValueError):
            pass  # Skip invalid max_tokens (e.g. empty string from form input)

    # Enable streaming usage for providers that support it
    if provider in ["OpenAI", "Anthropic"]:
        kwargs["stream_usage"] = True

    # Add provider-specific parameters
    if provider in {"IBM WatsonX", "IBM watsonx.ai"}:
        # For watsonx, url and project_id are required parameters
        # Try database first, then component values, then environment variables
        url_param = metadata.get("url_param", "url")
        project_id_param = metadata.get("project_id_param", "project_id")

        # Get all provider variables from database
        provider_vars = unified_models_module.get_all_variables_for_provider(user_id, provider)

        # Priority: component value > database value > env var
        watsonx_url_value = (
            watsonx_url if watsonx_url else provider_vars.get("WATSONX_URL") or os.environ.get("WATSONX_URL")
        )
        watsonx_project_id_value = (
            watsonx_project_id
            if watsonx_project_id
            else provider_vars.get("WATSONX_PROJECT_ID") or os.environ.get("WATSONX_PROJECT_ID")
        )

        has_url = bool(watsonx_url_value)
        has_project_id = bool(watsonx_project_id_value)

        if has_url and has_project_id:
            # Both provided - add them to kwargs
            kwargs[url_param] = watsonx_url_value
            kwargs[project_id_param] = watsonx_project_id_value
        elif has_url or has_project_id:
            # Only one provided - this is a misconfiguration
            missing = "project ID (WATSONX_PROJECT_ID)" if has_url else "URL (WATSONX_URL)"
            provided = "URL" if has_url else "project ID"
            msg = (
                f"IBM WatsonX requires both a URL and project ID. "
                f"You provided a watsonx {provided} but no {missing}. "
                f"Please configure the missing value in the component or set the environment variable."
            )
            raise ValueError(msg)
        # else: neither provided - let ChatWatsonx handle it (will fail with its own error)
    elif provider == "Ollama":
        # For Ollama, handle custom base_url with database > component > env var fallback
        base_url_param = metadata.get("base_url_param", "base_url")

        # Get all provider variables from database
        provider_vars = unified_models_module.get_all_variables_for_provider(user_id, provider)

        # Priority: component value > database value > env var
        ollama_base_url_value = (
            ollama_base_url
            if ollama_base_url
            else provider_vars.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_BASE_URL")
        )
        if ollama_base_url_value:
            kwargs[base_url_param] = ollama_base_url_value

    try:
        return model_class(**kwargs)
    except Exception as e:
        # If instantiation fails and it's WatsonX, provide additional context
        if provider in {"IBM WatsonX", "IBM watsonx.ai"} and ("url" in str(e).lower() or "project" in str(e).lower()):
            msg = (
                f"Failed to initialize IBM WatsonX model: {e}\n\n"
                "IBM WatsonX requires additional configuration parameters (API endpoint URL and project ID). "
                "This component may not support these parameters. "
                "Consider using the 'Language Model' component instead, which fully supports IBM WatsonX."
            )
            raise ValueError(msg) from e
        # Re-raise the original exception for other cases
        raise