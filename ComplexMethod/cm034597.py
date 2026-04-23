def create(
        self,
        messages: Messages,
        model: str = "",
        provider: Optional[ProviderType] = None,
        stream: Optional[bool] = False,
        proxy: Optional[str] = None,
        image: Optional[ImageType] = None,
        image_name: Optional[str] = None,
        response_format: Optional[dict] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[list[str], str]] = None,
        ignore_stream: Optional[bool] = False,
        raw: Optional[bool] = False,
        **kwargs
    ) -> Awaitable[ChatCompletion]:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        resolve_media(kwargs, image, image_name)
        if hasattr(model, "name"):
            model = model.get_long_name()
        if provider is None:
            provider = self.provider
            if provider is None:
                provider = AnyProvider
        if isinstance(provider, str):
            provider = convert_to_provider(provider)
        stop = [stop] if isinstance(stop, str) else stop
        if ignore_stream:
            kwargs["ignore_stream"] = True

        response = async_iter_run_tools(
            provider,
            model=model,
            messages=messages,
            stream=stream,
            **filter_none(
                proxy=self.client.proxy if proxy is None else proxy,
                max_tokens=max_tokens,
                stop=stop,
                api_key=self.client.api_key,
                base_url=self.client.base_url
            ),
            **kwargs
        )

        def fallback(response):
            provider_info = ProviderInfo(**provider.get_dict(), model=model)
            return async_iter_response(response, stream, response_format, max_tokens, stop, provider_info)

        if raw:
            async def raw_response(response):
                chunks = []
                started = False
                async for chunk in response:
                    if isinstance(chunk, JsonResponse):
                        yield chunk
                        started = True
                    else:
                        chunks.append(chunk)
                if not started:
                    for chunk in fallback(chunks):
                        yield chunk
            if stream:
                return raw_response(response)
            return anext(raw_response(response))
        if stream:
            return fallback(response)
        return anext(fallback(response))