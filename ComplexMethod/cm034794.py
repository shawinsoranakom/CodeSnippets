async def convert(
            file: UploadFile,
            path_provider: Optional[str] = None,
            model: Annotated[Optional[str], Form()] = None,
            provider: Annotated[Optional[str], Form()] = None,
            prompt: Annotated[Optional[str], Form()] = "Transcribe this audio"
        ):
            if path_provider is not None:
                provider = path_provider
            if provider is None:
                provider = "MarkItDown"
            try:
                provider = ProviderUtils.get_by_label(provider)
            except ValueError as e:
                if provider in model_map:
                    model = provider
                    provider = None 
                else:
                    return ErrorResponse.from_message(str(e), 404)
            kwargs = {"modalities": ["text"]}
            if provider == "MarkItDown":
                kwargs = {
                    "llm_client": self.client,
                }
            try:
                response = await self.client.chat.completions.create(
                    messages=prompt,
                    model=model,
                    provider=provider,
                    media=[[file.file, file.filename]],
                    **kwargs
                )
                return {"text": response.choices[0].message.content, "model": response.model, "provider": response.provider}
            except (ModelNotFoundError, ProviderNotFoundError) as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_404_NOT_FOUND)
            except MissingAuthError as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, None, HTTP_500_INTERNAL_SERVER_ERROR)