async def pa_chat_completions(
            config: ChatCompletionsConfig,
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(Api.security)] = None,
            provider_id: str = None,
        ):
            """OpenAI-compatible chat completions endpoint backed by PA providers.

            The PA provider is identified by its opaque ID either from the URL
            path (``/pa/{provider_id}/chat/completions``) or from the ``provider``
            field in the JSON body.  When both are absent the first available PA
            provider is used.
            """
            from g4f.mcp.pa_provider import get_pa_registry

            registry = get_pa_registry()
            pid = provider_id or config.provider
            if pid is None:
                listing = registry.list_providers()
                if not listing:
                    return ErrorResponse.from_message(
                        "No PA providers found in workspace", HTTP_404_NOT_FOUND
                    )
                pid = listing[0]["id"]

            provider_cls = registry.get_provider_class(pid)
            if provider_cls is None:
                return ErrorResponse.from_message(
                    f"PA provider '{pid}' not found", HTTP_404_NOT_FOUND
                )

            try:
                config.provider = None  # pass the class directly below
                if credentials is not None and credentials.credentials != "secret":
                    config.api_key = credentials.credentials

                response = self.client.chat.completions.create(
                    **filter_none(
                        **(
                            config.model_dump(exclude_none=True)
                            if hasattr(config, "model_dump")
                            else config.dict(exclude_none=True)
                        ),
                        **{
                            "conversation_id": None,
                            "provider": provider_cls,
                        },
                    ),
                )

                if not config.stream:
                    return await response

                async def streaming():
                    try:
                        async for chunk in response:
                            if not isinstance(chunk, BaseConversation):
                                yield (
                                    f"data: "
                                    f"{chunk.model_dump_json() if hasattr(chunk, 'model_dump_json') else chunk.json()}"
                                    f"\n\n"
                                )
                    except GeneratorExit:
                        pass
                    except Exception as e:
                        logger.exception(e)
                        yield f"data: {format_exception(e, config)}\n\n"
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