async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        media: MediaListType = None,
        api_key: str = None,
        api_endpoint: str = None,
        **kwargs
    ) -> AsyncResult:
        if not model:
            model = os.environ.get("AZURE_DEFAULT_MODEL", cls.default_model)
        if model in cls.model_aliases:
            model = cls.model_aliases[model]
        if not api_endpoint:
            if not cls.routes:
                cls.get_models()
            api_endpoint = cls.routes.get(model)
            if cls.routes and not api_endpoint:
                raise ModelNotFoundError(f"No API endpoint found for model: {model}")
        if not api_endpoint:
            api_endpoint = os.environ.get("AZURE_API_ENDPOINT")
        if cls.api_keys:
            api_key = cls.api_keys.get(model, cls.api_keys.get("default"))
            if not api_key:
                raise ValueError(f"API key is required for Azure provider. Ask for API key in the {cls.login_url} Discord server.")
        if api_endpoint and "/images/" in api_endpoint:
            prompt = format_media_prompt(messages, kwargs.get("prompt"))
            width, height = get_width_height(kwargs.get("aspect_ratio", "1:1"), kwargs.get("width"), kwargs.get("height"))
            output_format = kwargs.get("output_format", "png")
            form = None
            data = None
            if media:
                form = FormData()
                form.add_field("prompt", prompt)
                form.add_field("width", str(width))
                form.add_field("height", str(height))
                output_format = "png"
                for i in range(len(media)):
                    if media[i][1] is None and isinstance(media[i][0], str):
                        media[i] = media[i][0], os.path.basename(media[i][0])
                    media[i] = (to_bytes(media[i][0]), media[i][1])
                for image, image_name in media:
                    form.add_field(f"image", image, filename=image_name)
            else:
                api_endpoint = api_endpoint.replace("/edits", "/generations")
                data = {
                    "prompt": prompt,
                    "n": 1,
                    "width": width,
                    "height": height,
                    "output_format": output_format,
                }
            async with StreamSession(proxy=kwargs.get("proxy"), headers={
                "Authorization": f"Bearer {api_key}",
                "x-ms-model-mesh-model-name": model,
            }) as session:
                async with session.post(api_endpoint, data=form, json=data) as response:
                    data = await response.json()
                    await raise_for_status(response, data)
                    async for chunk in save_response_media(
                        data["data"][0]["b64_json"],
                        prompt,
                        content_type=f"image/{output_format.replace('jpg', 'jpeg')}"
                    ):
                        yield chunk
            return
        if model in cls.model_extra_body:
            for key, value in cls.model_extra_body[model].items():
                kwargs.setdefault(key, value)
            stream = False
        if cls.failed.get(model + api_key, 0) >= 3:
            raise MissingAuthError(f"API key has failed too many times.")
        try:
            async for chunk in super().create_async_generator(
                model=model,
                messages=messages,
                stream=stream,
                media=media,
                api_key=api_key,
                api_endpoint=api_endpoint,
                **kwargs
            ):
                yield chunk
        except MissingAuthError as e:
            cls.failed[model + api_key] = cls.failed.get(model + api_key, 0) + 1
            raise MissingAuthError(f"{e}. Ask for help in the {cls.login_url} Discord server.") from e