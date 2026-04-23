async def _generate_text(
        cls,
        model: str,
        messages: Messages,
        media: MediaListType,
        proxy: str,
        temperature: float,
        presence_penalty: float,
        top_p: float,
        frequency_penalty: float,
        response_format: Optional[dict],
        seed: Optional[int],
        cache: bool,
        stream: bool,
        extra_parameters: list[str],
        api_key: str,
        extra_body: dict,
        **kwargs
    ) -> AsyncResult:
        if not cache and seed is None:
            seed = random.randint(0, 2 ** 32)

        async with ClientSession(headers=DEFAULT_HEADERS, connector=get_connector(proxy=proxy)) as session:
            extra_body.update({param: kwargs[param] for param in extra_parameters if param in kwargs})
            if model in cls.audio_models:
                if "audio" in extra_body and extra_body.get("audio", {}).get("voice") is None:
                    extra_body["audio"]["voice"] = cls.default_voice
                elif "audio" not in extra_body:
                    extra_body["audio"] = {"voice": cls.default_voice}
                if extra_body.get("audio", {}).get("format") is None:
                    extra_body["audio"]["format"] = "mp3"
                    stream = False
                if "modalities" not in extra_body:
                    extra_body["modalities"] = ["text", "audio"]
            data = filter_none(
                messages=list(render_messages(messages, media)),
                model=model,
                temperature=temperature,
                presence_penalty=presence_penalty,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                response_format=response_format,
                stream=stream,
                seed=None if "tools" in extra_body else seed,
                **extra_body
            )
            if (not api_key or api_key.startswith("g4f_") or api_key.startswith("gfs_")) and cls.balance and cls.balance > 0:
                endpoint = cls.worker_api_endpoint
            elif api_key:
                endpoint = cls.gen_text_api_endpoint
            else:
                endpoint = cls.text_api_endpoint
            headers = None
            if api_key:
                headers = {"authorization": f"Bearer {api_key}"}
            yield JsonRequest.from_dict(data)
            async with session.post(endpoint, json=data, headers=headers) as response:
                if response.status in (400, 500):
                    debug.error(f"Error: {response.status} - Bad Request: {data}")
                async for chunk in read_response(response, stream, format_media_prompt(messages), cls.get_dict(),
                                                 kwargs.get("download_media", True)):
                    yield chunk