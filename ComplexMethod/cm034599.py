def get_model_and_provider(model    : Union[Model, str], 
                           provider : Union[ProviderType, str, None], 
                           stream   : bool = False,
                           ignore_working: bool = False,
                           ignore_stream: bool = False,
                           logging: bool = True,
                           has_images: bool = False) -> tuple[str, ProviderType]:
    """
    Retrieves the model and provider based on input parameters.

    Args:
        model (Union[Model, str]): The model to use, either as an object or a string identifier.
        provider (Union[ProviderType, str, None]): The provider to use, either as an object, a string identifier, or None.
        stream (bool): Indicates if the operation should be performed as a stream.
        ignored (list[str], optional): List of provider names to be ignored.
        ignore_working (bool, optional): If True, ignores the working status of the provider.
        ignore_stream (bool, optional): If True, ignores the streaming capability of the provider.

    Returns:
        tuple[str, ProviderType]: A tuple containing the model name and the provider type.

    Raises:
        ProviderNotFoundError: If the provider is not found.
        ModelNotFoundError: If the model is not found.
        ProviderNotWorkingError: If the provider is not working.
        StreamNotSupportedError: If streaming is not supported by the provider.
    """
    if debug.version_check:
        debug.version_check = False
        version.utils.check_version()

    if isinstance(provider, str):
        provider = convert_to_provider(provider)

    if not provider:
        # Check config.yaml custom model routes first
        if isinstance(model, str):
            try:
                from ..providers.config_provider import RouterConfig, ConfigModelProvider
                route_config = RouterConfig.get(model)
                if route_config is not None:
                    config_provider = ConfigModelProvider(route_config)
                    debug.last_provider = config_provider
                    debug.last_model = model
                    if logging:
                        debug.log(f"Using config.yaml route for model {model!r}")
                    return model, config_provider
            except Exception as e:
                debug.error("config.yaml: Error resolving config route:", e)

        if isinstance(model, str):
            if model in ModelUtils.convert:
                model = ModelUtils.convert[model]

        if not model:
            if has_images:
                model = default_vision
                provider = default_vision.best_provider
            else:
                model = default
                provider = model.best_provider
        elif isinstance(model, str):
            if model in ProviderUtils.convert:
                provider = ProviderUtils.convert[model]
                model = getattr(provider, "default_model", "")
            else:
                raise ModelNotFoundError(f'Model not found: {model}')
        elif isinstance(model, Model):
            provider = model.best_provider
        else:
            raise ValueError(f"Unexpected type: {type(model)}")
    if not provider:
        raise ProviderNotFoundError(f'No provider found for model: {model}')

    provider_name = provider.__name__ if hasattr(provider, "__name__") else type(provider).__name__

    if isinstance(model, Model):
        model = model.get_long_name()

    if not ignore_working and not provider.working:
        raise ProviderNotWorkingError(f"{provider_name} is not working")

    if isinstance(provider, BaseRetryProvider):
        if not ignore_working:
            provider.providers = [p for p in provider.providers if p.working]

    if not ignore_stream and not provider.supports_stream and stream:
        raise StreamNotSupportedError(f'{provider_name} does not support "stream" argument')

    if logging:
        if model:
            debug.log(f'Using {provider_name} provider and {model} model')
        else:
            debug.log(f'Using {provider_name} provider')

    debug.last_provider = provider
    debug.last_model = model

    return model, provider