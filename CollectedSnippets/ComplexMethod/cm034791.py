async def chat_completions(
            config: ChatCompletionsConfig,
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(Api.security)] = None,
            provider: str = None,
            conversation_id: str = None,
            x_user: Annotated[str | None, Header()] = None,
        ):
            if provider is None:
                provider = config.provider
            if provider is None:
                provider = AppConfig.provider
            try:
                provider = ProviderUtils.get_by_label(provider).__name__
            except ValueError as e:
                if provider in model_map:
                    config.model = provider
                    provider = None
                elif provider is not None:
                    return ErrorResponse.from_message(str(e), 404)
            try:
                config.provider = provider
                if config.conversation_id is None:
                    config.conversation_id = conversation_id
                if config.timeout is None:
                    config.timeout = AppConfig.timeout
                if config.stream_timeout is None and config.stream:
                    config.stream_timeout = AppConfig.stream_timeout
                if credentials is not None and credentials.credentials != "secret":
                    config.api_key = credentials.credentials

                conversation = config.conversation
                if conversation:
                    conversation = JsonConversation(**conversation)
                elif config.conversation_id is not None and config.provider is not None:
                    if config.conversation_id in self.conversations:
                        if config.provider in self.conversations[config.conversation_id]:
                            conversation = self.conversations[config.conversation_id][config.provider]

                if config.image is not None:
                    try:
                        is_data_an_media(config.image)
                    except ValueError as e:
                        return ErrorResponse.from_message(f"The image you send must be a data URI. Example: data:image/jpeg;base64,...", status_code=HTTP_422_UNPROCESSABLE_ENTITY)
                if config.media is None:
                    config.media = config.images
                if config.media is not None:
                    for image in config.media:
                        try:
                            is_data_an_media(image[0], image[1])
                        except ValueError as e:
                            example = json.dumps({"media": [["data:image/jpeg;base64,...", "filename.jpg"]]})
                            return ErrorResponse.from_message(f'The media you send must be a data URIs. Example: {example}', status_code=HTTP_422_UNPROCESSABLE_ENTITY)

                # Create the completion response
                response = self.client.chat.completions.create(
                    **filter_none(
                        **{
                            "model": AppConfig.model,
                            "provider": AppConfig.provider,
                            "proxy": AppConfig.proxy,
                            **(config.model_dump(exclude_none=True) if hasattr(config, "model_dump") else config.dict(exclude_none=True)),
                            **{
                                "conversation_id": None,
                                "conversation": conversation,
                                "user": x_user,
                            }
                        },
                        ignored=AppConfig.ignored_providers
                    ),
                )

                if not config.stream:
                    return await response

                async def streaming():
                    try:
                        async for chunk in response:
                            if isinstance(chunk, BaseConversation):
                                if config.conversation_id is not None and config.provider is not None:
                                    if config.conversation_id not in self.conversations:
                                        self.conversations[config.conversation_id] = {}
                                    self.conversations[config.conversation_id][config.provider] = chunk
                            else:
                                yield f"data: {chunk.model_dump_json() if hasattr(chunk, 'model_dump_json') else chunk.json()}\n\n"
                    except GeneratorExit:
                        pass
                    except Exception as e:
                        logger.exception(e)
                        yield f'data: {format_exception(e, config)}\n\n'
                    yield "data: [DONE]\n\n"

                return StreamingResponse(streaming(), media_type="text/event-stream")

            except (ModelNotFoundError, ProviderNotFoundError) as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_404_NOT_FOUND)
            except (MissingAuthError, NoValidHarFileError) as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.exception(e)
                return ErrorResponse.from_exception(e, config, HTTP_500_INTERNAL_SERVER_ERROR)