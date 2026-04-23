async def create_async_generator(
        self,
        model: str,
        messages: Messages,
        ignored: list[str] = [],
        api_key: str = None,
        conversation: JsonConversation = None,
        **kwargs
    ) -> AsyncResult:
        exceptions = {}
        started: bool = False

        for provider in self.get_providers(ignored):
            self.last_provider = provider
            alias = _resolve_model(provider, model)
            debug.log(f"Using {provider.__name__} provider with model {alias}")
            yield ProviderInfo(**provider.get_dict(), model=alias)
            extra_body = _prepare_provider_kwargs(provider, api_key, conversation, kwargs)
            try:
                method = get_async_provider_method(provider)
                response = method(model=alias, messages=messages, **extra_body)
                async for chunk in response:
                    if isinstance(chunk, JsonConversation):
                        if conversation is None:
                            conversation = JsonConversation()
                        setattr(conversation, provider.__name__, chunk.get_dict())
                        yield conversation
                    elif chunk:
                        yield chunk
                        if is_content(chunk):
                            started = True
                if started:
                    return
            except Exception as e:
                exceptions[provider.__name__] = e
                debug.error(f"{provider.__name__}:", e)
                if started:
                    raise e

        raise_exceptions(exceptions)