async def generate_image(
            request: Request,
            config: ImageGenerationConfig,
            provider: str = None,
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(Api.security)] = None
        ):
            if provider is None:
                provider = config.provider
            if provider is None:
                provider = AppConfig.provider
            try:
                provider = ProviderUtils.get_by_label(provider)
            except ValueError as e:
                if provider in model_map:
                    config.model = provider
                    provider = None
                elif provider is not None:
                    return ErrorResponse.from_message(str(e), 404)
            config.provider = provider
            if config.api_key is None and credentials is not None and credentials.credentials != "secret":
                config.api_key = credentials.credentials
            try:
                response = await self.client.images.generate(
                    **config.dict(exclude_none=True),
                )
                for image in response.data:
                    if hasattr(image, "url") and image.url.startswith("/"):
                        image.url = f"{request.base_url}{image.url.lstrip('/')}"
                return response
            except (ModelNotFoundError, ProviderNotFoundError) as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_404_NOT_FOUND)
            except MissingAuthError as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_500_INTERNAL_SERVER_ERROR)