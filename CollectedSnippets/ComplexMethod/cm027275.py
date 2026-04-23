async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure: vol.Schema | None = None,
    ) -> None:
        """Generate an answer for the chat log."""
        settings = {**self.entry.data, **self.subentry.data}

        client = self.entry.runtime_data
        model = settings[CONF_MODEL]

        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        message_history: MessageHistory = MessageHistory(
            [_convert_content(content) for content in chat_log.content]
        )
        max_messages = int(settings.get(CONF_MAX_HISTORY, DEFAULT_MAX_HISTORY))
        self._trim_history(message_history, max_messages)

        output_format: dict[str, Any] | None = None
        if structure:
            output_format = convert(
                structure,
                custom_serializer=(
                    chat_log.llm_api.custom_serializer
                    if chat_log.llm_api
                    else llm.selector_serializer
                ),
            )

        # Get response
        # To prevent infinite loops, we limit the number of iterations
        for _iteration in range(MAX_TOOL_ITERATIONS):
            try:
                response_generator = await client.chat(
                    model=model,
                    # Make a copy of the messages because we mutate the list later
                    messages=list(message_history.messages),
                    tools=tools,
                    stream=True,
                    # keep_alive requires specifying unit. In this case, seconds
                    keep_alive=f"{settings.get(CONF_KEEP_ALIVE, DEFAULT_KEEP_ALIVE)}s",
                    options={CONF_NUM_CTX: settings.get(CONF_NUM_CTX, DEFAULT_NUM_CTX)},
                    think=settings.get(CONF_THINK),
                    format=output_format,
                )
            except (ollama.RequestError, ollama.ResponseError) as err:
                _LOGGER.error("Unexpected error talking to Ollama server: %s", err)
                raise HomeAssistantError(
                    f"Sorry, I had a problem talking to the Ollama server: {err}"
                ) from err

            message_history.messages.extend(
                [
                    _convert_content(content)
                    async for content in chat_log.async_add_delta_content_stream(
                        self.entity_id, _transform_stream(response_generator)
                    )
                ]
            )

            if not chat_log.unresponded_tool_results:
                break