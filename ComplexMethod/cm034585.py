async def create_async_generator(
        self,
        model: str,
        messages: Messages,
        **kwargs
    ) -> AsyncResult:
        exceptions = {}
        started = False

        if self.single_provider_retry:
            provider = self.providers[0]
            self.last_provider = provider
            for attempt in range(self.max_retries):
                try:
                    debug.log(f"Using {provider.__name__} provider (attempt {attempt + 1})")
                    method = get_async_provider_method(provider)
                    response = method(model=model, messages=messages, **kwargs)
                    async for chunk in response:
                        yield chunk
                        if is_content(chunk):
                            started = True
                    if started:
                        return
                except Exception as e:
                    exceptions[provider.__name__] = e
                    if debug.logging:
                        print(f"{provider.__name__}: {e.__class__.__name__}: {e}")
            raise_exceptions(exceptions)
        else:
            async for chunk in super().create_async_generator(model, messages, **kwargs):
                yield chunk