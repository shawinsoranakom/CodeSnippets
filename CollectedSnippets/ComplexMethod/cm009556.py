def _create_message_from_message_type(
    message_type: str,
    content: str,
    name: str | None = None,
    tool_call_id: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    id: str | None = None,
    **additional_kwargs: Any,
) -> BaseMessage:
    """Create a message from a `Message` type and content string.

    Args:
        message_type: the type of the message (e.g., `'human'`, `'ai'`, etc.).
        content: the content string.
        name: the name of the message.
        tool_call_id: the tool call id.
        tool_calls: the tool calls.
        id: the id of the message.
        additional_kwargs: additional keyword arguments.

    Returns:
        a message of the appropriate type.

    Raises:
        ValueError: if the message type is not one of `'human'`, `'user'`, `'ai'`,
            `'assistant'`, `'function'`, `'tool'`, `'system'`, or
            `'developer'`.
    """
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if tool_call_id is not None:
        kwargs["tool_call_id"] = tool_call_id
    if additional_kwargs:
        if response_metadata := additional_kwargs.pop("response_metadata", None):
            kwargs["response_metadata"] = response_metadata
        kwargs["additional_kwargs"] = additional_kwargs
        additional_kwargs.update(additional_kwargs.pop("additional_kwargs", {}))
    if id is not None:
        kwargs["id"] = id
    if tool_calls is not None:
        kwargs["tool_calls"] = []
        for tool_call in tool_calls:
            # Convert OpenAI-format tool call to LangChain format.
            if "function" in tool_call:
                args = tool_call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args, strict=False)
                kwargs["tool_calls"].append(
                    {
                        "name": tool_call["function"]["name"],
                        "args": args,
                        "id": tool_call["id"],
                        "type": "tool_call",
                    }
                )
            else:
                kwargs["tool_calls"].append(tool_call)
    if message_type in {"human", "user"}:
        if example := kwargs.get("additional_kwargs", {}).pop("example", False):
            kwargs["example"] = example
        message: BaseMessage = HumanMessage(content=content, **kwargs)
    elif message_type in {"ai", "assistant"}:
        if example := kwargs.get("additional_kwargs", {}).pop("example", False):
            kwargs["example"] = example
        message = AIMessage(content=content, **kwargs)
    elif message_type in {"system", "developer"}:
        if message_type == "developer":
            kwargs["additional_kwargs"] = kwargs.get("additional_kwargs") or {}
            kwargs["additional_kwargs"]["__openai_role__"] = "developer"
        message = SystemMessage(content=content, **kwargs)
    elif message_type == "function":
        message = FunctionMessage(content=content, **kwargs)
    elif message_type == "tool":
        artifact = kwargs.get("additional_kwargs", {}).pop("artifact", None)
        status = kwargs.get("additional_kwargs", {}).pop("status", None)
        if status is not None:
            kwargs["status"] = status
        message = ToolMessage(content=content, artifact=artifact, **kwargs)
    elif message_type == "remove":
        message = RemoveMessage(**kwargs)
    else:
        msg = (
            f"Unexpected message type: '{message_type}'. Use one of 'human',"
            f" 'user', 'ai', 'assistant', 'function', 'tool', 'system', or 'developer'."
        )
        msg = create_message(message=msg, error_code=ErrorCode.MESSAGE_COERCION_FAILURE)
        raise ValueError(msg)
    return message