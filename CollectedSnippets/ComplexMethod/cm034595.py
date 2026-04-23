async def async_create_variation(
        self,
        *,
        image: ImageType,
        image_name: str = None,
        prompt: str = "Create a variation of this image",
        model: Optional[str] = None,
        provider: Optional[ProviderType] = None,
        response_format: Optional[str] = None,
        proxy: Optional[str] = None,
        **kwargs
    ) -> ImagesResponse:
        provider_handler = await self.get_provider_handler(model, provider, OpenaiAccount)
        provider_name = provider_handler.__name__ if hasattr(provider_handler, "__name__") else type(provider_handler).__name__
        if proxy is None:
            proxy = self.client.proxy
        resolve_media(kwargs, image, image_name)
        error = None
        response = None
        if isinstance(provider_handler, IterListProvider):
            for provider in provider_handler.providers:
                try:
                    response = await self._generate_image_response(provider, provider.__name__, model, prompt, **kwargs)
                    if response is not None:
                        provider_name = provider.__name__
                        break
                except Exception as e:
                    error = e
                    debug.error(f"{provider.__name__}:", e)
        else:
            response = await self._generate_image_response(provider_handler, provider_name, model, prompt, **kwargs)
        if response is None:
            if error is not None:
                raise error
            raise NoMediaResponseError(f"No media response from {provider_name}")
        return await self._process_image_response(
            response,
            model,
            provider_name,
            kwargs.get("download_media", True),
            response_format,
            proxy
        )