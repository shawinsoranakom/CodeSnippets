async def create_async_generator(
        self,
        model: str,
        messages: Messages,
        ignored: list[str] = [],
        api_key: str = None,
        conversation: JsonConversation = None,
        **kwargs
    ) -> AsyncResult:
        """
        Asynchronously create a completion, rotating through providers on failure.
        """
        exceptions: Dict[str, Exception] = {}

        for _ in range(len(self.providers)):
            provider = self._get_current_provider()
            self._rotate_provider()
            self.last_provider = provider

            if provider.get_parent() in ignored:
                continue

            alias = _resolve_model(provider, model)

            debug.log(f"Attempting provider: {provider.__name__} with model: {alias}")
            yield ProviderInfo(**provider.get_dict(), model=alias)

            extra_body = _prepare_provider_kwargs(provider, api_key, conversation, kwargs)

            try:
                method = get_async_provider_method(provider)
                response = method(model=alias, messages=messages, **extra_body)
                started = False
                async for chunk in response:
                    if isinstance(chunk, JsonConversation):
                        if conversation is None: conversation = JsonConversation()
                        setattr(conversation, provider.__name__, chunk.get_dict())
                        yield conversation
                    elif chunk:
                        yield chunk
                        if is_content(chunk):
                            started = True
                if started:
                    provider.live += 1
                    return # Success
            except Exception as e:
                provider.live -= 1
                exceptions[provider.__name__] = e
                debug.error(f"{provider.__name__} failed: {e}")

        raise_exceptions(exceptions)