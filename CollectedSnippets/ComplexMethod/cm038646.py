def response_input_to_harmony(
    response_msg: ResponseInputOutputItem,
    prev_responses: list[ResponseOutputItem | ResponseReasoningItem],
) -> Message | None:
    """Convert a single ResponseInputOutputItem into a Harmony Message.

    Returns None for reasoning items with empty or absent content so
    the caller can skip them.
    """
    if not isinstance(response_msg, dict):
        response_msg = response_msg.model_dump()
    if "type" not in response_msg or response_msg["type"] == "message":
        role = response_msg["role"]
        content = response_msg["content"]
        # Add prefix for developer messages.
        # <|start|>developer<|message|># Instructions {instructions}<|end|>
        text_prefix = "Instructions:\n" if role == "developer" else ""
        if isinstance(content, str):
            msg = Message.from_role_and_content(role, text_prefix + content)
        else:
            contents = [TextContent(text=text_prefix + c["text"]) for c in content]
            msg = Message.from_role_and_contents(role, contents)
        if role == "assistant":
            msg = msg.with_channel("final")
    elif response_msg["type"] == "function_call_output":
        call_id = response_msg["call_id"]
        call_response: ResponseFunctionToolCall | None = None
        for prev_response in reversed(prev_responses):
            if (
                isinstance(prev_response, ResponseFunctionToolCall)
                and prev_response.call_id == call_id
            ):
                call_response = prev_response
                break
        if call_response is None:
            raise ValueError(f"No call message found for {call_id}")
        msg = Message.from_author_and_content(
            Author.new(Role.TOOL, f"functions.{call_response.name}"),
            response_msg["output"],
        )
    elif response_msg["type"] == "reasoning":
        content = response_msg.get("content")
        if content and len(content) >= 1:
            reasoning_text = "\n".join(item["text"] for item in content)
            msg = Message.from_role_and_content(Role.ASSISTANT, reasoning_text)
            msg = msg.with_channel("analysis")
        else:
            return None
    elif response_msg["type"] == "function_call":
        msg = Message.from_role_and_content(Role.ASSISTANT, response_msg["arguments"])
        msg = msg.with_channel("commentary")
        msg = msg.with_recipient(f"functions.{response_msg['name']}")
        msg = msg.with_content_type("json")
    else:
        raise ValueError(f"Unknown input type: {response_msg['type']}")
    return msg