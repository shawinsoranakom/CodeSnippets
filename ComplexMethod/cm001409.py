def _make_single_result_message(
        episode: Episode, result: ActionResult
    ) -> ChatMessage:
        """Create a result message for a single tool call."""
        if result.status == "success":
            return (
                ToolResultMessage(
                    content=str(result.outputs),
                    tool_call_id=episode.action.raw_message.tool_calls[0].id,
                )
                if episode.action.raw_message.tool_calls
                else ChatMessage.user(
                    f"{episode.action.use_tool.name} returned: "
                    + (
                        f"```\n{result.outputs}\n```"
                        if "\n" in str(result.outputs)
                        else f"`{result.outputs}`"
                    )
                )
            )
        elif result.status == "error":
            return (
                ToolResultMessage(
                    content=f"{result.reason}\n\n{result.error or ''}".strip(),
                    is_error=True,
                    tool_call_id=episode.action.raw_message.tool_calls[0].id,
                )
                if episode.action.raw_message.tool_calls
                else ChatMessage.user(
                    f"{episode.action.use_tool.name} raised an error: ```\n"
                    f"{result.reason}\n"
                    "```"
                )
            )
        else:
            # ActionInterruptedByHuman - user provided feedback instead of executing
            # Must return ToolResultMessage to satisfy API requirements (both Anthropic
            # and OpenAI require tool_use/function_call to be followed by tool_result)
            feedback_content = (
                f"Command not executed. User provided feedback: {result.feedback}"
            )
            return (
                ToolResultMessage(
                    content=feedback_content,
                    is_error=True,
                    tool_call_id=episode.action.raw_message.tool_calls[0].id,
                )
                if episode.action.raw_message.tool_calls
                else ChatMessage.user(feedback_content)
            )