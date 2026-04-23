async def async_add_assistant_content(
        self,
        content: AssistantContent | ToolResultContent,
        /,
        tool_call_tasks: dict[str, asyncio.Task] | None = None,
    ) -> AsyncGenerator[ToolResultContent]:
        """Add assistant content and execute tool calls.

        tool_call_tasks can contains tasks for tool calls that are already in progress.

        This method is an async generator and will yield the tool results as they come in.
        """
        LOGGER.debug("Adding assistant content: %s", content)
        self.content.append(content)

        if (
            not isinstance(content, AssistantContent)
            or content.tool_calls is None
            or all(tool_call.external for tool_call in content.tool_calls)
        ):
            return

        if self.llm_api is None:
            raise ValueError("No LLM API configured")

        if tool_call_tasks is None:
            tool_call_tasks = {}
        for tool_input in content.tool_calls:
            if tool_input.id not in tool_call_tasks and not tool_input.external:
                tool_call_tasks[tool_input.id] = self.hass.async_create_task(
                    self.llm_api.async_call_tool(tool_input),
                    name=f"llm_tool_{tool_input.id}",
                )

        for tool_input in content.tool_calls:
            if tool_input.external:
                continue

            LOGGER.debug(
                "Tool call: %s(%s)", tool_input.tool_name, tool_input.tool_args
            )

            try:
                tool_result = await tool_call_tasks[tool_input.id]
            except (HomeAssistantError, vol.Invalid) as e:
                tool_result = {"error": type(e).__name__}
                if str(e):
                    tool_result["error_text"] = str(e)
            LOGGER.debug("Tool response: %s", tool_result)

            response_content = ToolResultContent(
                agent_id=content.agent_id,
                tool_call_id=tool_input.id,
                tool_name=tool_input.tool_name,
                tool_result=tool_result,
            )
            self.content.append(response_content)
            _async_notify_subscribers(
                self.hass,
                self.conversation_id,
                ChatLogEventType.CONTENT_ADDED,
                {
                    "content": response_content.as_dict(),
                },
            )
            yield response_content