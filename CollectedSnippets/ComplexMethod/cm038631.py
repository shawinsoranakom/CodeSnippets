def _construct_single_message_from_response_item(
    item: ResponseInputOutputItem,
) -> ChatCompletionMessageParam:
    if isinstance(item, ResponseFunctionToolCall):
        # Append the function call as a tool call.
        return ChatCompletionAssistantMessageParam(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageToolCallParam(
                    id=item.call_id,
                    function=FunctionCallTool(
                        name=item.name,
                        arguments=item.arguments,
                    ),
                    type="function",
                )
            ],
        )
    elif isinstance(item, ResponseReasoningItem):
        reasoning = ""
        if item.encrypted_content:
            raise ValueError("Encrypted content is not supported.")
        elif item.content and len(item.content) >= 1:
            reasoning = item.content[0].text
        elif len(item.summary) >= 1:
            reasoning = item.summary[0].text
            logger.warning(
                "Using summary text as reasoning content for item %s. "
                "Please use content instead of summary for "
                "reasoning items.",
                item.id,
            )
        return {
            "role": "assistant",
            "reasoning": reasoning,
        }
    elif isinstance(item, ResponseOutputMessage):
        return {
            "role": "assistant",
            "content": item.content[0].text,
        }
    elif isinstance(item, ResponseFunctionToolCallOutputItem):
        return ChatCompletionToolMessageParam(
            role="tool",
            content=item.output,
            tool_call_id=item.call_id,
        )
    elif isinstance(item, dict) and item.get("type") == "function_call_output":
        # Append the function call output as a tool message.
        return ChatCompletionToolMessageParam(
            role="tool",
            content=item.get("output"),
            tool_call_id=item.get("call_id"),
        )
    return item