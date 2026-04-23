def count_tokens_openai(
    messages: Sequence[LLMMessage],
    model: str,
    *,
    add_name_prefixes: bool = False,
    tools: Sequence[Tool | ToolSchema] = [],
    model_family: str = ModelFamily.UNKNOWN,
    include_name_in_message: bool = True,
) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        trace_logger.warning(f"Model {model} not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0

    # Message tokens.
    for message in messages:
        num_tokens += tokens_per_message
        oai_message = to_oai_type(
            message,
            prepend_name=add_name_prefixes,
            model=model,
            model_family=model_family,
            include_name_in_message=include_name_in_message,
        )
        for oai_message_part in oai_message:
            for key, value in oai_message_part.items():
                if value is None:
                    continue

                if isinstance(message, UserMessage) and isinstance(value, list):
                    typed_message_value = cast(List[ChatCompletionContentPartParam], value)

                    assert len(typed_message_value) == len(
                        message.content
                    ), "Mismatch in message content and typed message value"

                    # We need image properties that are only in the original message
                    for part, content_part in zip(typed_message_value, message.content, strict=False):
                        if isinstance(content_part, Image):
                            # TODO: add detail parameter
                            num_tokens += calculate_vision_tokens(content_part)
                        elif isinstance(part, str):
                            num_tokens += len(encoding.encode(part))
                        else:
                            try:
                                serialized_part = json.dumps(part)
                                num_tokens += len(encoding.encode(serialized_part))
                            except TypeError:
                                trace_logger.warning(f"Could not convert {part} to string, skipping.")
                else:
                    if not isinstance(value, str):
                        try:
                            value = json.dumps(value)
                        except TypeError:
                            trace_logger.warning(f"Could not convert {value} to string, skipping.")
                            continue
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>

    # Tool tokens.
    oai_tools = convert_tools(tools)
    for tool in oai_tools:
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
                        elif field == "anyOf":
                            tool_tokens -= 3
                            for o in v["anyOf"]:  # type: ignore
                                tool_tokens += 3
                                tool_tokens += len(encoding.encode(str(o["type"])))  # pyright: ignore
                        elif field == "default":
                            tool_tokens += 2
                            tool_tokens += len(encoding.encode(json.dumps(v["default"])))
                        elif field == "title":
                            tool_tokens += 2
                            tool_tokens += len(encoding.encode(str(v["title"])))  # pyright: ignore
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

    if oai_tools:
        num_tokens += 12
    return num_tokens