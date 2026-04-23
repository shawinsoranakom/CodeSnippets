async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        timeout: int = 120,
        conversation: JsonConversation = None,
        media: MediaListType = None,
        api_key: str = None,
        api_endpoint: str = None,
        base_url: str = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
        stop: Union[str, list[str]] = None,
        stream: bool = None,
        prompt: str = None,
        user: str = None,
        headers: dict = None,
        impersonate: str = None,
        download_media: bool = True,
        extra_parameters: list[str] = ["tools", "parallel_tool_calls", "tool_choice", "reasoning_effort", "logit_bias", "modalities", "audio", "stream_options", "include_reasoning", "response_format", "max_completion_tokens", "reasoning_effort", "search_settings"],
        extra_body: dict = None,
        **kwargs
    ) -> AsyncResult:
        if api_key is None and cls.api_key is not None:
            api_key = cls.api_key
        if cls.needs_auth and api_key is None:
            raise MissingAuthError('Add a "api_key"')
        async with StreamSession(
            proxy=proxy,
            headers=cls.get_headers(stream, api_key, headers),
            timeout=timeout,
            impersonate=impersonate,
        ) as session:
            model = cls.get_model(model, api_key=api_key, base_url=base_url)
            if base_url is None:
                base_url = cls.base_url if cls.is_provider_api_key(api_key) else cls.backup_url

            # Proxy for image generation feature
            if model and model in cls.image_models:
                prompt = format_media_prompt(messages, prompt)
                size = use_aspect_ratio({"width": kwargs.get("width"), "height": kwargs.get("height")}, kwargs.get("aspect_ratio", None))
                size = {"size": f"{size['width']}x{size['height']}", **size} if cls.use_image_size and "width" in size and "height" in size else size
                data = {"prompt": prompt, "model": model, **size}

                # Handle media if provided
                if media is not None:
                    data["image_url"] = next(iter([data for data, _ in media if data and isinstance(data, str) and data.startswith("http://") or data.startswith("https://")]), None)
                async with session.post(f"{base_url.rstrip('/')}/images/generations", json=data, ssl=cls.ssl) as response:
                    data = await response.json()
                    cls.raise_error(data, response.status)
                    model = data.get("model")
                    if model:
                        yield ProviderInfo(**cls.get_dict(), model=model)
                    await raise_for_status(response)
                    yield ImageResponse([f"data:image/png;base64,{image['b64_json']}" if image.get("url") is None else image["url"] for image in data["data"]], prompt)
                return

            if stream or stream is None:
                kwargs.setdefault("stream_options", {"include_usage": True})
            extra_parameters = {key: kwargs[key] for key in extra_parameters if key in kwargs}
            if extra_body is None:
                extra_body = {}
            data = filter_none(
                messages=list(render_messages(messages, media)),
                model=model,
                temperature=temperature,
                max_tokens=max_tokens if max_tokens is not None else cls.max_tokens,
                top_p=top_p,
                stop=stop,
                stream="audio" not in extra_parameters if stream is None else stream,
                user=user if cls.add_user else None,
                conversation=conversation.get_dict() if conversation else None,
                **extra_parameters,
                **extra_body
            )
            if api_endpoint is None:
                if api_endpoint is None:
                    api_endpoint = cls.api_endpoint
                if api_endpoint is None:
                    api_endpoint = f"{base_url.rstrip('/')}/chat/completions"
            yield JsonRequest.from_dict(data)
            async with session.post(api_endpoint, json=data, ssl=cls.ssl) as response:
                async for chunk in read_response(response, stream, prompt, cls.get_dict(), download_media):
                    yield chunk