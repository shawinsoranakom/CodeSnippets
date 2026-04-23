def _make_result_messages(
        episode: Episode, result: ActionResult
    ) -> list[ChatMessage]:
        """Create result messages for all tool calls in an episode.

        When multiple tools are called in parallel, we need to create a
        ToolResultMessage for EACH tool_call to satisfy API requirements
        (both Anthropic and OpenAI require tool_use to be followed by tool_result).

        Args:
            episode: The episode containing the action and its raw message
            result: The result of executing the action(s)

        Returns:
            List of ChatMessage objects (ToolResultMessage or user message)
        """
        tool_calls = (
            episode.action.raw_message.tool_calls
            if episode.action.raw_message.tool_calls
            else []
        )

        # Single tool call or no tool calls - use simple logic
        if len(tool_calls) <= 1:
            return [ActionHistoryComponent._make_single_result_message(episode, result)]

        # Multiple tool calls - create a result for each
        messages: list[ChatMessage] = []

        # Get outputs dict if parallel execution returned a dict
        outputs_dict: dict = {}
        errors_list: list[str] = []
        if result.status == "success" and isinstance(result.outputs, dict):
            outputs_dict = result.outputs
            errors_list = outputs_dict.pop("_errors", [])
        elif result.status == "error":
            # All tools failed - create error results for all
            for tool_call in tool_calls:
                messages.append(
                    ToolResultMessage(
                        content=f"{result.reason}\n\n{result.error or ''}".strip(),
                        is_error=True,
                        tool_call_id=tool_call.id,
                    )
                )
            return messages

        # Create result message for each tool call
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_id = tool_call.id

            # Check if this tool's result is in the outputs
            if tool_name in outputs_dict:
                output = outputs_dict[tool_name]
                messages.append(
                    ToolResultMessage(
                        content=str(output),
                        tool_call_id=tool_id,
                    )
                )
            else:
                # Check if there's an error for this tool
                error_msg = next(
                    (e for e in errors_list if e.startswith(f"{tool_name}:")), None
                )
                if error_msg:
                    messages.append(
                        ToolResultMessage(
                            content=error_msg,
                            is_error=True,
                            tool_call_id=tool_id,
                        )
                    )
                else:
                    # Fallback - tool not found in results
                    messages.append(
                        ToolResultMessage(
                            content="No result returned",
                            is_error=True,
                            tool_call_id=tool_id,
                        )
                    )

        return messages