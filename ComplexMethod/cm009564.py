def _get_message_openai_role(message: BaseMessage) -> str:
    if isinstance(message, AIMessage):
        return "assistant"
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, ToolMessage):
        return "tool"
    if isinstance(message, SystemMessage):
        role = message.additional_kwargs.get("__openai_role__", "system")
        if not isinstance(role, str):
            msg = f"Expected '__openai_role__' to be a str, got {type(role).__name__}"
            raise TypeError(msg)
        return role
    if isinstance(message, FunctionMessage):
        return "function"
    if isinstance(message, ChatMessage):
        return message.role
    msg = f"Unknown BaseMessage type {message.__class__}."
    raise ValueError(msg)