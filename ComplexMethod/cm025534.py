async def _prepare_chat_for_generation(
        self,
        chat_log: conversation.ChatLog,
        messages: list[ResponseInputItemParam],
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Prepare kwargs for Cloud LLM from the chat log."""

        last_content: Any = chat_log.content[-1]
        if last_content.role == "user" and last_content.attachments:
            files = await self._async_prepare_files_for_prompt(last_content.attachments)

            last_message = cast(dict[str, Any], messages[-1])
            assert (
                last_message["type"] == "message"
                and last_message["role"] == "user"
                and isinstance(last_message["content"], str)
            )
            last_message["content"] = [
                {"type": "input_text", "text": last_message["content"]},
                *files,
            ]

        tools: list[ToolParam] = []
        tool_choice: str | None = None

        if chat_log.llm_api:
            ha_tools: list[ToolParam] = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

            if ha_tools:
                if not chat_log.unresponded_tool_results:
                    tools = ha_tools
                    tool_choice = "auto"
                else:
                    tools = []
                    tool_choice = "none"

        web_search = WebSearchToolParam(
            type="web_search",
            search_context_size="medium",
        )
        tools.append(web_search)

        response_kwargs: dict[str, Any] = {
            "messages": messages,
            "conversation_id": chat_log.conversation_id,
        }

        if response_format is not None:
            response_kwargs["response_format"] = response_format
        if tools is not None:
            response_kwargs["tools"] = tools
        if tool_choice is not None:
            response_kwargs["tool_choice"] = tool_choice

        response_kwargs["stream"] = True

        return response_kwargs