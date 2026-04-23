async def create_async_generator(
        cls, model: str, messages: Messages, media: MediaListType = None, **kwargs
    ) -> AsyncResult:
        if not model and media is not None:
            model = cls.default_vision_model
        is_started = False
        random.shuffle(cls.providers)
        for provider in cls.providers:
            if model in provider.model_aliases or model in provider.get_models():
                alias = provider.model_aliases[model] if model in provider.model_aliases else model
                async for chunk in provider.create_async_generator(alias, messages, media=media, **kwargs):
                    is_started = True
                    yield chunk
            if is_started:
                return