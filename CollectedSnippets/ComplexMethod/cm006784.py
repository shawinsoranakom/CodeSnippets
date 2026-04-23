def get_embeddings(
    model,
    user_id: UUID | str | None = None,
    api_key=None,
    *,
    api_base=None,
    dimensions=None,
    chunk_size=None,
    request_timeout=None,
    max_retries=None,
    show_progress_bar=None,
    model_kwargs=None,
    watsonx_url=None,
    watsonx_project_id=None,
    watsonx_truncate_input_tokens=None,
    watsonx_input_text=None,
    ollama_base_url=None,
) -> Any:
    """Instantiate an embeddings model from a model selection dict."""
    # Resolve helpers via package namespace so tests patching
    # lfx.base.models.unified_models.<name> keep working.
    from lfx.base.models import unified_models as unified_models_module

    # Coerce provider-specific string params
    ollama_base_url = _to_str(ollama_base_url)
    watsonx_url = _to_str(watsonx_url)
    watsonx_project_id = _to_str(watsonx_project_id)

    # Passthrough: already-instantiated Embeddings object from a connection
    try:
        from langchain_core.embeddings import Embeddings as BaseEmbeddings

        if isinstance(model, BaseEmbeddings):
            return model
    except ImportError:
        pass

    # Validate input
    if not model or not isinstance(model, list) or len(model) == 0:
        msg = "An embedding model selection is required"
        raise ValueError(msg)

    model_dict = model[0]
    model_name = model_dict.get("name")
    provider = model_dict.get("provider")
    metadata = model_dict.get("metadata", {})

    # --- resolve API key -----------------------------------------------------
    api_key = unified_models_module.get_api_key_for_provider(user_id, provider, api_key)
    if not api_key and provider != "Ollama":
        provider_variable_map = unified_models_module.get_model_provider_variable_mapping()
        variable_name = provider_variable_map.get(provider, f"{provider.upper().replace(' ', '_')}_API_KEY")
        msg = (
            f"{provider} API key is required. "
            f"Please provide it in the component or configure it globally as {variable_name}."
        )
        raise ValueError(msg)

    if not model_name:
        msg = "Embedding model name is required"
        raise ValueError(msg)

    # Get embedding class from metadata
    embedding_class_name = metadata.get("embedding_class")
    if not embedding_class_name:
        msg = f"No embedding class defined in metadata for {model_name}"
        raise ValueError(msg)
    embedding_class = unified_models_module.get_embedding_class(embedding_class_name)

    # --- build kwargs from param_mapping -------------------------------------
    param_mapping: dict[str, str] = metadata.get("param_mapping", {})
    if not param_mapping:
        msg = (
            f"Parameter mapping not found in metadata for model '{model_name}' (provider: {provider}). "
            "This usually means the model was saved with an older format that is no longer recognized. "
            "Please re-select the embedding model in the component configuration."
        )
        raise ValueError(msg)

    kwargs: dict[str, Any] = {}

    # Model name
    if "model" in param_mapping:
        kwargs[param_mapping["model"]] = model_name
    elif "model_id" in param_mapping:
        kwargs[param_mapping["model_id"]] = model_name

    # API key
    if "api_key" in param_mapping and api_key:
        kwargs[param_mapping["api_key"]] = api_key

    # Optional parameters - only add when both a value is supplied *and* the
    # provider's param_mapping declares the corresponding key.
    optional_params: dict[str, Any] = {
        "api_base": _to_str(api_base) or None,
        "dimensions": int(dimensions) if dimensions else None,
        "chunk_size": int(chunk_size) if chunk_size else None,
        "request_timeout": float(request_timeout) if request_timeout else None,
        "max_retries": int(max_retries) if max_retries else None,
        "show_progress_bar": show_progress_bar,
        "model_kwargs": model_kwargs if model_kwargs else None,
    }

    # Watson-specific parameters
    if provider in {"IBM WatsonX", "IBM watsonx.ai"}:
        watsonx_provider_vars = unified_models_module.get_all_variables_for_provider(user_id, provider)
        url_value = watsonx_url or watsonx_provider_vars.get("WATSONX_URL") or os.environ.get("WATSONX_URL")
        pid_value = (
            watsonx_project_id
            or watsonx_provider_vars.get("WATSONX_PROJECT_ID")
            or os.environ.get("WATSONX_PROJECT_ID")
        )

        has_url = bool(url_value)
        has_project_id = bool(pid_value)

        if has_url and has_project_id:
            if "url" in param_mapping:
                kwargs[param_mapping["url"]] = url_value
            if "project_id" in param_mapping:
                kwargs[param_mapping["project_id"]] = pid_value
        elif has_url or has_project_id:
            missing = "project ID (WATSONX_PROJECT_ID)" if has_url else "URL (WATSONX_URL)"
            provided = "URL" if has_url else "project ID"
            msg = (
                f"IBM WatsonX requires both a URL and project ID. "
                f"You provided a watsonx {provided} but no {missing}. "
                f"Please configure the missing value in the component or set the environment variable."
            )
            raise ValueError(msg)

        # Build WatsonX embed params (truncate_input_tokens, return_options)
        watsonx_params = {}
        if watsonx_truncate_input_tokens is not None:
            try:
                from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames

                watsonx_params[EmbedTextParamsMetaNames.TRUNCATE_INPUT_TOKENS] = int(watsonx_truncate_input_tokens)
            except ImportError:
                watsonx_params["truncate_input_tokens"] = int(watsonx_truncate_input_tokens)
        if watsonx_input_text is not None:
            try:
                from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames

                watsonx_params[EmbedTextParamsMetaNames.RETURN_OPTIONS] = {"input_text": bool(watsonx_input_text)}
            except ImportError:
                watsonx_params["return_options"] = {"input_text": bool(watsonx_input_text)}
        if watsonx_params:
            kwargs["params"] = watsonx_params

    # Ollama-specific parameters
    if provider == "Ollama" and "base_url" in param_mapping:
        provider_vars = unified_models_module.get_all_variables_for_provider(user_id, provider)
        base_url_value = (
            ollama_base_url
            or provider_vars.get("OLLAMA_BASE_URL")
            or os.environ.get("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        )
        kwargs[param_mapping["base_url"]] = base_url_value

    # Add optional parameters if they have values and are mapped
    for param_name, param_value in optional_params.items():
        if param_value is not None and param_name in param_mapping:
            # Google wraps timeout in a dict
            if (
                param_name == "request_timeout"
                and provider == "Google Generative AI"
                and isinstance(param_value, (int, float))
            ):
                kwargs[param_mapping[param_name]] = {"timeout": param_value}
            else:
                kwargs[param_mapping[param_name]] = param_value

    try:
        return embedding_class(**kwargs)
    except Exception as e:
        if provider == "IBM WatsonX" and ("url" in str(e).lower() or "project" in str(e).lower()):
            msg = (
                f"Failed to initialize IBM WatsonX embedding model: {e}\n\n"
                "IBM WatsonX requires additional configuration parameters (API endpoint URL and project ID)."
            )
            raise ValueError(msg) from e
        raise