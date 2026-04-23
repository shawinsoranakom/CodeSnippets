def _message_from_dict(message: dict) -> BaseMessage:
    type_ = message["type"]
    if type_ == "human":
        return HumanMessage(**message["data"])
    if type_ == "ai":
        return AIMessage(**message["data"])
    if type_ == "system":
        return SystemMessage(**message["data"])
    if type_ == "chat":
        return ChatMessage(**message["data"])
    if type_ == "function":
        return FunctionMessage(**message["data"])
    if type_ == "tool":
        return ToolMessage(**message["data"])
    if type_ == "remove":
        return RemoveMessage(**message["data"])
    if type_ == "AIMessageChunk":
        return AIMessageChunk(**message["data"])
    if type_ == "HumanMessageChunk":
        return HumanMessageChunk(**message["data"])
    if type_ == "FunctionMessageChunk":
        return FunctionMessageChunk(**message["data"])
    if type_ == "ToolMessageChunk":
        return ToolMessageChunk(**message["data"])
    if type_ == "SystemMessageChunk":
        return SystemMessageChunk(**message["data"])
    if type_ == "ChatMessageChunk":
        return ChatMessageChunk(**message["data"])
    msg = f"Got unexpected message type: {type_}"
    raise ValueError(msg)