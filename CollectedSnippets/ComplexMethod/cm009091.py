def _construct_responses_api_payload(
    messages: Sequence[BaseMessage], payload: dict
) -> dict:
    # Rename legacy parameters
    for legacy_token_param in ["max_tokens", "max_completion_tokens"]:
        if legacy_token_param in payload:
            payload["max_output_tokens"] = payload.pop(legacy_token_param)
    if "reasoning_effort" in payload and "reasoning" not in payload:
        payload["reasoning"] = {"effort": payload.pop("reasoning_effort")}

    # Remove temperature parameter for models that don't support it in responses API
    # gpt-5-chat supports temperature, and gpt-5 models with reasoning.effort='none'
    # also support temperature
    model = payload.get("model") or ""
    if (
        model.startswith("gpt-5")
        and ("chat" not in model)  # gpt-5-chat supports
        and (payload.get("reasoning") or {}).get("effort") != "none"
    ):
        payload.pop("temperature", None)

    payload["input"] = _construct_responses_api_input(messages)
    if tools := payload.pop("tools", None):
        new_tools: list = []
        for tool in tools:
            # chat api: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}, "strict": ...}}  # noqa: E501
            # responses api: {"type": "function", "name": "...", "description": "...", "parameters": {...}, "strict": ...}  # noqa: E501
            if tool["type"] == "function" and "function" in tool:
                extra = {k: v for k, v in tool.items() if k not in ("type", "function")}
                new_tools.append({"type": "function", **tool["function"], **extra})
            else:
                if tool["type"] == "image_generation":
                    # Handle partial images (not yet supported)
                    if "partial_images" in tool:
                        msg = (
                            "Partial image generation is not yet supported "
                            "via the LangChain ChatOpenAI client. Please "
                            "drop the 'partial_images' key from the image_generation "
                            "tool."
                        )
                        raise NotImplementedError(msg)
                    if payload.get("stream") and "partial_images" not in tool:
                        # OpenAI requires this parameter be set; we ignore it during
                        # streaming.
                        tool = {**tool, "partial_images": 1}
                    else:
                        pass

                new_tools.append(tool)

        payload["tools"] = new_tools
    if tool_choice := payload.pop("tool_choice", None):
        # chat api: {"type": "function", "function": {"name": "..."}}
        # responses api: {"type": "function", "name": "..."}
        if (
            isinstance(tool_choice, dict)
            and tool_choice["type"] == "function"
            and "function" in tool_choice
        ):
            payload["tool_choice"] = {"type": "function", **tool_choice["function"]}
        else:
            payload["tool_choice"] = tool_choice

    # Structured output
    if schema := payload.pop("response_format", None):
        # For pydantic + non-streaming case, we use responses.parse.
        # Otherwise, we use responses.create.
        strict = payload.pop("strict", None)
        if not payload.get("stream") and _is_pydantic_class(schema):
            payload["text_format"] = schema
        else:
            if _is_pydantic_class(schema):
                schema_dict = schema.model_json_schema()
                strict = True
            else:
                schema_dict = schema
            if schema_dict == {"type": "json_object"}:  # JSON mode
                if "text" in payload and isinstance(payload["text"], dict):
                    payload["text"]["format"] = {"type": "json_object"}
                else:
                    payload["text"] = {"format": {"type": "json_object"}}
            elif (
                (
                    response_format := _convert_to_openai_response_format(
                        schema_dict, strict=strict
                    )
                )
                and (isinstance(response_format, dict))
                and (response_format["type"] == "json_schema")
            ):
                format_value = {"type": "json_schema", **response_format["json_schema"]}
                if "text" in payload and isinstance(payload["text"], dict):
                    payload["text"]["format"] = format_value
                else:
                    payload["text"] = {"format": format_value}
            else:
                pass

    verbosity = payload.pop("verbosity", None)
    if verbosity is not None:
        if "text" in payload and isinstance(payload["text"], dict):
            payload["text"]["verbosity"] = verbosity
        else:
            payload["text"] = {"verbosity": verbosity}

    return payload