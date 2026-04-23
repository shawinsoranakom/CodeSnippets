async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        proxy: str = None,
        cache: bool = None,
        api_key: str = None,
        extra_body: dict = None,
        # Image generation parameters
        prompt: str = None,
        aspect_ratio: str = None,
        width: int = None,
        height: int = None,
        seed: Optional[int] = None,
        nologo: bool = True,
        private: bool = False,
        enhance: bool = None,
        safe: bool = False,
        transparent: bool = False,
        n: int = 1,
        # Text generation parameters
        media: MediaListType = None,
        temperature: float = None,
        presence_penalty: float = None,
        top_p: float = None,
        frequency_penalty: float = None,
        response_format: Optional[dict] = None,
        extra_parameters: list[str] = ["tools", "parallel_tool_calls", "tool_choice", "reasoning_effort",
                                        "logit_bias", "voice", "modalities", "audio"],
        **kwargs
    ) -> AsyncResult:
        if cache is None:
            cache = kwargs.get("action") is None or kwargs.get("action") != "variant"
        if extra_body is None:
            extra_body = {}
        if not model:
            has_audio = "audio" in kwargs or "audio" in kwargs.get("modalities", [])
            if not has_audio and media is not None:
                for media_data, filename in media:
                    if is_data_an_audio(media_data, filename):
                        has_audio = True
                        break
            model = "openai-audio" if has_audio else cls.default_model
        if not api_key:
            api_key = AuthManager.load_api_key(cls)
        if cls.get_models(api_key=api_key, timeout=kwargs.get("timeout", 15)):
            if model in cls.model_aliases:
                model = cls.model_aliases[model]
        debug.log(f"Using model: {model}")
        alias = cls.swap_model_aliases.get(model, model)
        if alias in cls.image_models or alias in cls.video_models:
            async for chunk in cls._generate_image(
                model="gptimage" if model == "transparent" else model,
                alias=alias,
                prompt=format_media_prompt(messages, prompt),
                media=media,
                proxy=proxy,
                aspect_ratio=aspect_ratio,
                width=width,
                height=height,
                seed=seed,
                cache=cache,
                nologo=nologo,
                private=private,
                enhance=enhance,
                safe=safe,
                transparent=transparent or model == "transparent",
                n=n,
                api_key=api_key
            ):
                yield chunk
        else:
            if prompt is not None and len(messages) == 1:
                messages = [{
                    "role": "user",
                    "content": prompt
                }]
            async for result in cls._generate_text(
                    model=model,
                    messages=messages,
                    media=media,
                    proxy=proxy,
                    temperature=temperature,
                    presence_penalty=presence_penalty,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    response_format=response_format,
                    seed=seed,
                    cache=cache,
                    stream=stream,
                    extra_parameters=extra_parameters,
                    api_key=api_key,
                    extra_body=extra_body,
                    **kwargs
            ):
                yield result