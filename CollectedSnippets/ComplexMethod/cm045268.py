def count_tokens_ollama(messages: Sequence[LLMMessage], model: str, *, tools: Sequence[Tool | ToolSchema] = []) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        trace_logger.warning(f"Model {model} not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    num_tokens = 0

    # Message tokens.
    for message in messages:
        num_tokens += tokens_per_message
        ollama_message = to_ollama_type(message)
        for ollama_message_part in ollama_message:
            if isinstance(message.content, Image):
                num_tokens += calculate_vision_tokens(message.content)
            elif ollama_message_part.content is not None:
                num_tokens += len(encoding.encode(ollama_message_part.content))
    # TODO: every model family has its own message sequence.
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>

    # Tool tokens.
    ollama_tools = convert_tools(tools)
    for tool in ollama_tools:
        function = tool["function"]
        tool_tokens = len(encoding.encode(function["name"]))
        if "description" in function:
            tool_tokens += len(encoding.encode(function["description"]))
        tool_tokens -= 2
        if "parameters" in function:
            parameters = function["parameters"]
            if "properties" in parameters:
                assert isinstance(parameters["properties"], dict)
                for propertiesKey in parameters["properties"]:  # pyright: ignore
                    assert isinstance(propertiesKey, str)
                    tool_tokens += len(encoding.encode(propertiesKey))
                    v = parameters["properties"][propertiesKey]  # pyright: ignore
                    for field in v:  # pyright: ignore
                        if field == "type":
                            tool_tokens += 2
                            tool_tokens += len(encoding.encode(v["type"]))  # pyright: ignore
                        elif field == "description":
                            tool_tokens += 2
                            tool_tokens += len(encoding.encode(v["description"]))  # pyright: ignore
                        elif field == "enum":
                            tool_tokens -= 3
                            for o in v["enum"]:  # pyright: ignore
                                tool_tokens += 3
                                tool_tokens += len(encoding.encode(o))  # pyright: ignore
                        else:
                            trace_logger.warning(f"Not supported field {field}")
                tool_tokens += 11
                if len(parameters["properties"]) == 0:  # pyright: ignore
                    tool_tokens -= 2
        num_tokens += tool_tokens
    num_tokens += 12
    return num_tokens