async def _generate_image_response(
        self,
        provider_handler: ProviderType,
        provider_name: str,
        model: str,
        prompt: str,
        prompt_prefix: str = "Generate a image: ",
        api_key: str = None,
        **kwargs
    ) -> MediaResponse:
        messages = [{"role": "user", "content": f"{prompt_prefix}{prompt}"}]
        items: list[MediaResponse] = []
        if isinstance(api_key, dict):
            api_key = api_key.get(provider_handler.get_parent())
        if hasattr(provider_handler, "create_async_generator"):
            async for item in provider_handler.create_async_generator(
                model,
                messages,
                stream=True,
                prompt=prompt,
                api_key=api_key,
                **kwargs
            ):
                if isinstance(item, (MediaResponse, AudioResponse)) and not isinstance(item, HiddenResponse):
                    items.append(item)
        elif hasattr(provider_handler, "create_completion"):
            for item in provider_handler.create_completion(
                model,
                messages,
                True,
                prompt=prompt,
                api_key=api_key,
                **kwargs
            ):
                if isinstance(item, (MediaResponse, AudioResponse)) and not isinstance(item, HiddenResponse):
                    items.append(item)
        else:
            raise ValueError(f"Provider {provider_name} does not support image generation")
        urls = []
        for item in items:
            if isinstance(item, AudioResponse):
                urls.append(item.to_uri())
            elif isinstance(item.urls, str):
                urls.append(item.urls)
            elif isinstance(item.urls, list):
                urls.extend(item.urls)
        if not urls:
            return None
        alt = getattr(items[0], "alt", "")
        return MediaResponse(urls, alt, items[0].options)