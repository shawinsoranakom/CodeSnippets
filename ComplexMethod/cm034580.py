async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        media: MediaListType = None,
        ignored: list[str] = [],
        api_key: Union[str, dict[str, str]] = None,
        **kwargs,
    ) -> AsyncResult:
        providers = []
        if not model or model == cls.default_model:
            model = ""
            has_image = False
            has_audio = False
            if not has_audio and media is not None:
                for media_data, filename in media:
                    if is_data_an_audio(media_data, filename):
                        has_audio = True
                        break
                    has_image = True
            # Do not override provider selection just because tools are present.
            # Tool calling is an API-level feature; routing should be based on model/media.
            if "audio" in kwargs or "audio" in kwargs.get("modalities", []):
                if kwargs.get("audio", {}).get("language") is None:
                    providers = [PollinationsAI, OpenAIFM, Gemini]
                else:
                    providers = [PollinationsAI, OpenAIFM, EdgeTTS, gTTS]
            elif has_audio:
                providers = [PollinationsAI, Microsoft_Phi_4_Multimodal, MarkItDown]
            elif has_image:
                providers = models.default_vision.best_provider.providers
            else:
                providers = models.default.best_provider.providers
        elif model in RouterConfig.routes:
            async for chunk in ConfigModelProvider(RouterConfig.routes.get(model)).create_async_generator(
                model, messages, stream=stream, media=media, api_key=api_key, **kwargs
            ):
                yield chunk
            return
        elif model in Provider.__map__:
            provider = Provider.__map__[model]
            if provider.working and provider.get_parent() not in ignored:
                model = None
                providers.append(provider)
        elif model and ":" in model:
            provider, submodel = model.split(":", maxsplit=1)
            if hasattr(Provider, provider):
                provider = getattr(Provider, provider)
                if provider.working and provider.get_parent() not in ignored:
                    providers.append(provider)
                    model = submodel
        else:
            if model not in cls.model_map:
                if model in cls.model_aliases:
                    model = cls.model_aliases[model]
            if model in cls.model_map:
                for provider, alias in cls.model_map[model].items():
                    provider = Provider.__map__[provider]
                    if model not in provider.model_aliases:
                        provider.model_aliases[model] = alias
                    providers.append(provider)
        if not providers:
            for provider in PROVIDERS_LIST_2 + PROVIDERS_LIST_3:
                try:
                    if model in provider.get_models():
                        providers.append(provider)
                    elif model in provider.model_aliases:
                        providers.append(provider)
                except Exception as e:
                    debug.error(
                        f"Error checking provider {provider.__name__} for model {model}:",
                        e,
                    )
        providers = [
            provider
            for provider in providers
            if provider.working and provider.get_parent() not in ignored
        ]
        providers = list(
            {provider.__name__: provider for provider in providers}.values()
        )

        # Free-first routing: if no api_key is provided, prioritize providers that
        # don't require auth before trying auth-gated providers.
        has_api_key = bool(api_key) or bool(kwargs.get("api_key"))
        if not has_api_key:
            providers.sort(key=lambda p: bool(getattr(p, "needs_auth", False)))

        if len(providers) == 0:
            raise ModelNotFoundError(
                f"AnyProvider: Model {model} not found in any provider."
            )

        debug.log(
            f"AnyProvider: Using providers: {[provider.__name__ for provider in providers]} for model '{model}'"
        )

        async for chunk in RotatedProvider(providers).create_async_generator(
            model, messages, stream=stream, media=media, api_key=api_key, **kwargs
        ):
            yield chunk