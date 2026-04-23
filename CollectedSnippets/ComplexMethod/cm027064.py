async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure: vol.Schema | None = None,
        default_max_tokens: int | None = None,
        max_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> None:
        """Generate an answer for the chat log."""
        options = self.subentry.data

        tools: ToolListUnion | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        # Using search grounding allows the model to retrieve information from the web,
        # however, it may interfere with how the model decides to use some tools, or entities
        # for example weather entity may be disregarded if the model chooses to Google it.
        if options.get(CONF_USE_GOOGLE_SEARCH_TOOL) is True:
            tools = tools or []
            tools.append(Tool(google_search=GoogleSearch()))

        model_name = options.get(CONF_CHAT_MODEL, self.default_model)
        # Avoid INVALID_ARGUMENT Developer instruction is not enabled for <model>
        supports_system_instruction = (
            "gemma" not in model_name
            and "gemini-2.0-flash-preview-image-generation" not in model_name
        )

        prompt_content = cast(
            conversation.SystemContent,
            chat_log.content[0],
        )

        if prompt_content.content:
            prompt = prompt_content.content
        else:
            raise HomeAssistantError("Invalid prompt content")

        messages: list[Content | ContentDict] = []

        # Google groups tool results, we do not. Group them before sending.
        tool_results: list[conversation.ToolResultContent] = []

        for chat_content in chat_log.content[1:-1]:
            if chat_content.role == "tool_result":
                tool_results.append(chat_content)
                continue

            if (
                not isinstance(chat_content, conversation.ToolResultContent)
                and chat_content.content == ""
            ):
                # Skipping is not possible since the number of function calls need to match the number of function responses
                # and skipping one would mean removing the other and hence this would prevent a proper chat log
                chat_content = replace(chat_content, content=" ")

            if tool_results:
                messages.append(_create_google_tool_response_content(tool_results))
                tool_results.clear()

            messages.append(_convert_content(chat_content))

        # The SDK requires the first message to be a user message
        # This is not the case if user used `start_conversation`
        # Workaround from https://github.com/googleapis/python-genai/issues/529#issuecomment-2740964537
        if messages and (
            (isinstance(messages[0], Content) and messages[0].role != "user")
            or (isinstance(messages[0], dict) and messages[0]["role"] != "user")
        ):
            messages.insert(
                0,
                Content(role="user", parts=[Part.from_text(text=" ")]),
            )

        if tool_results:
            messages.append(_create_google_tool_response_content(tool_results))
        generateContentConfig = self.create_generate_content_config()
        generateContentConfig.tools = tools or None
        generateContentConfig.system_instruction = (
            prompt if supports_system_instruction else None
        )
        generateContentConfig.automatic_function_calling = (
            AutomaticFunctionCallingConfig(disable=True, maximum_remote_calls=None)
        )
        if structure:
            generateContentConfig.response_mime_type = "application/json"
            generateContentConfig.response_schema = _format_schema(
                convert(
                    structure,
                    custom_serializer=(
                        chat_log.llm_api.custom_serializer
                        if chat_log.llm_api
                        else llm.selector_serializer
                    ),
                )
            )

        if not supports_system_instruction:
            messages = [
                Content(role="user", parts=[Part.from_text(text=prompt)]),
                Content(role="model", parts=[Part.from_text(text="Ok")]),
                *messages,
            ]
        chat = self._genai_client.aio.chats.create(
            model=model_name, history=messages, config=generateContentConfig
        )
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)
        chat_request: list[PartUnionDict] = [user_message.content]
        if user_message.attachments:
            chat_request.extend(
                await async_prepare_files_for_prompt(
                    self.hass,
                    self._genai_client,
                    [(a.path, a.mime_type) for a in user_message.attachments],
                )
            )

        # To prevent infinite loops, we limit the number of iterations
        for _iteration in range(max_iterations):
            try:
                chat_response_generator = await chat.send_message_stream(
                    message=chat_request
                )
            except (
                APIError,
                ClientError,
                ValueError,
            ) as err:
                LOGGER.error("Error sending message: %s %s", type(err), err)
                error = ERROR_GETTING_RESPONSE
                raise HomeAssistantError(error) from err

            chat_request = list(
                _create_google_tool_response_parts(
                    [
                        content
                        async for content in chat_log.async_add_delta_content_stream(
                            self.entity_id,
                            _transform_stream(chat_response_generator),
                        )
                        if isinstance(content, conversation.ToolResultContent)
                    ]
                )
            )

            if not chat_log.unresponded_tool_results:
                break