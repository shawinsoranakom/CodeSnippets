def get_supported_llm_models(
    config: OpenHandsConfig,
    verified_models: list[str] | None = None,
) -> ModelsResponse:
    """Collect every model available to this server and return structured data.

    The returned ``ModelsResponse`` contains:

    * a flat list of ``provider/model`` strings (bare LiteLLM names are
      prefixed with the correct provider),
    * a list of *verified* model names (the OpenHands-curated subset),
    * the set of verified providers, and
    * the recommended default model.

    Args:
        config: The OpenHands configuration.
        verified_models: Optional list of ``"openhands/<name>"`` strings
            from the database (SaaS mode).  When provided these replace the
            hardcoded ``OPENHANDS_MODELS``.
    """
    litellm_model_list = litellm.model_list + list(litellm.model_cost.keys())
    litellm_model_list_without_bedrock = bedrock.remove_error_modelId(
        litellm_model_list
    )
    # TODO: for bedrock, this is using the default config
    llm_config: LLMConfig = config.get_llm_config()
    bedrock_model_list: list[str] = []
    if (
        llm_config.aws_region_name
        and llm_config.aws_access_key_id
        and llm_config.aws_secret_access_key
    ):
        bedrock_model_list = bedrock.list_foundation_models(
            llm_config.aws_region_name,
            llm_config.aws_access_key_id.get_secret_value(),
            llm_config.aws_secret_access_key.get_secret_value(),
        )
    model_list = litellm_model_list_without_bedrock + bedrock_model_list
    for llm_config in config.llms.values():
        ollama_base_url = llm_config.ollama_base_url
        if llm_config.model.startswith('ollama'):
            if not ollama_base_url:
                ollama_base_url = llm_config.base_url
        if ollama_base_url:
            ollama_url = ollama_base_url.strip('/') + '/api/tags'
            try:
                ollama_models_list = httpx.get(ollama_url, timeout=3).json()['models']  # noqa: ASYNC100
                for model in ollama_models_list:
                    model_list.append('ollama/' + model['name'])
                break
            except httpx.HTTPError as e:
                logger.error(f'Error getting OLLAMA models: {e}')

    openhands_models = get_openhands_models(verified_models)

    # Assign canonical provider prefixes to bare LiteLLM names, then dedupe.
    all_models = (
        openhands_models + CLARIFAI_MODELS + [_assign_provider(m) for m in model_list]
    )
    unique_models = sorted(set(all_models))

    return ModelsResponse(
        models=unique_models,
        verified_models=_derive_verified_models(openhands_models),
        verified_providers=VERIFIED_PROVIDERS,
        default_model=DEFAULT_OPENHANDS_MODEL,
    )