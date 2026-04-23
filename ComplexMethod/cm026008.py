async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure_name: str | None = None,
        structure: vol.Schema | None = None,
    ) -> None:
        """Generate an answer for the chat log."""

        model = self.model
        if self.subentry.data.get(CONF_WEB_SEARCH):
            model = f"{model}:online"

        extra_body: dict[str, Any] = {"require_parameters": True}

        model_args = {
            "model": model,
            "user": chat_log.conversation_id,
            "extra_headers": {
                "X-Title": "Home Assistant",
                "HTTP-Referer": "https://www.home-assistant.io/integrations/open_router",
            },
            "extra_body": extra_body,
        }

        tools: list[ChatCompletionFunctionToolParam] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        if tools:
            model_args["tools"] = tools

        model_args["messages"] = [
            m
            for content in chat_log.content
            if (m := _convert_content_to_chat_message(content))
        ]

        last_content = chat_log.content[-1]

        # Handle attachments by adding them to the last user message
        if last_content.role == "user" and last_content.attachments:
            last_message: ChatCompletionMessageParam = model_args["messages"][-1]
            assert last_message["role"] == "user" and isinstance(
                last_message["content"], str
            )
            # Encode files with base64 and append them to the text prompt
            files = await async_prepare_files_for_prompt(
                self.hass,
                [(a.path, a.mime_type) for a in last_content.attachments],
            )
            last_message["content"] = [
                {"type": "text", "text": last_message["content"]},
                *files,
            ]

        if structure:
            if TYPE_CHECKING:
                assert structure_name is not None
            model_args["response_format"] = ResponseFormatJSONSchema(
                type="json_schema",
                json_schema=_format_structured_output(
                    structure_name, structure, chat_log.llm_api
                ),
            )

        client = self.entry.runtime_data

        for _iteration in range(MAX_TOOL_ITERATIONS):
            try:
                result = await client.chat.completions.create(**model_args)
            except openai.OpenAIError as err:
                LOGGER.error("Error talking to API: %s", err)
                raise HomeAssistantError("Error talking to API") from err

            if not result.choices:
                LOGGER.error("API returned empty choices")
                raise HomeAssistantError("API returned empty response")

            result_message = result.choices[0].message

            model_args["messages"].extend(
                [
                    msg
                    async for content in chat_log.async_add_delta_content_stream(
                        self.entity_id, _transform_response(result_message)
                    )
                    if (msg := _convert_content_to_chat_message(content))
                ]
            )
            if not chat_log.unresponded_tool_results:
                break