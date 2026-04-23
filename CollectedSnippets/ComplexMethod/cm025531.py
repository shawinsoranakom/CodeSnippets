def _convert_content_to_param(
    chat_content: Iterable[conversation.Content],
) -> list[ResponseInputItemParam]:
    """Convert any native chat message for this agent to the native format."""
    messages: list[ResponseInputItemParam] = []
    reasoning_summary: list[str] = []
    web_search_calls: dict[str, dict[str, Any]] = {}

    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            if (
                content.tool_name == "web_search_call"
                and content.tool_call_id in web_search_calls
            ):
                web_search_call = web_search_calls.pop(content.tool_call_id)
                web_search_call["status"] = content.tool_result.get(
                    "status", "completed"
                )
                messages.append(cast("ResponseInputItemParam", web_search_call))
            else:
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": content.tool_call_id,
                        "output": json_dumps(content.tool_result),
                    }
                )
            continue

        if content.content:
            role: Literal["user", "assistant", "system", "developer"] = content.role
            if role == "system":
                role = "developer"
            messages.append(
                {"type": "message", "role": role, "content": content.content}
            )

        if isinstance(content, conversation.AssistantContent):
            if content.tool_calls:
                for tool_call in content.tool_calls:
                    if (
                        tool_call.external
                        and tool_call.tool_name == "web_search_call"
                        and "action" in tool_call.tool_args
                    ):
                        web_search_calls[tool_call.id] = {
                            "type": "web_search_call",
                            "id": tool_call.id,
                            "action": tool_call.tool_args["action"],
                            "status": "completed",
                        }
                    else:
                        messages.append(
                            {
                                "type": "function_call",
                                "name": tool_call.tool_name,
                                "arguments": json_dumps(tool_call.tool_args),
                                "call_id": tool_call.id,
                            }
                        )

            if content.thinking_content:
                reasoning_summary.append(content.thinking_content)

            if isinstance(content.native, ResponseReasoningItem):
                messages.append(
                    {
                        "type": "reasoning",
                        "id": content.native.id,
                        "summary": (
                            [
                                {
                                    "type": "summary_text",
                                    "text": summary,
                                }
                                for summary in reasoning_summary
                            ]
                            if content.thinking_content
                            else []
                        ),
                        "encrypted_content": content.native.encrypted_content,
                    }
                )
                reasoning_summary = []

            elif isinstance(content.native, ImageGenerationCall):
                messages.append(
                    cast(ImageGenerationCallParam, content.native.to_dict())
                )

    return messages