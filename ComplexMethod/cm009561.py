def convert_to_openai_messages(
    messages: MessageLikeRepresentation | Sequence[MessageLikeRepresentation],
    *,
    text_format: Literal["string", "block"] = "string",
    include_id: bool = False,
    pass_through_unknown_blocks: bool = True,
) -> dict | list[dict]:
    """Convert LangChain messages into OpenAI message dicts.

    Args:
        messages: Message-like object or iterable of objects whose contents are
            in OpenAI, Anthropic, Bedrock Converse, or VertexAI formats.
        text_format: How to format string or text block contents:
            - `'string'`:
                If a message has a string content, this is left as a string. If
                a message has content blocks that are all of type `'text'`, these
                are joined with a newline to make a single string. If a message has
                content blocks and at least one isn't of type `'text'`, then
                all blocks are left as dicts.
            - `'block'`:
                If a message has a string content, this is turned into a list
                with a single content block of type `'text'`. If a message has
                content blocks these are left as is.
        include_id: Whether to include message IDs in the openai messages, if they
            are present in the source messages.
        pass_through_unknown_blocks: Whether to include content blocks with unknown
            formats in the output. If `False`, an error is raised if an unknown
            content block is encountered.

    Raises:
        ValueError: if an unrecognized `text_format` is specified, or if a message
            content block is missing expected keys.

    Returns:
        The return type depends on the input type:

        - dict:
            If a single message-like object is passed in, a single OpenAI message
            dict is returned.
        - list[dict]:
            If a sequence of message-like objects are passed in, a list of OpenAI
            message dicts is returned.

    Example:
        ```python
        from langchain_core.messages import (
            convert_to_openai_messages,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )

        messages = [
            SystemMessage([{"type": "text", "text": "foo"}]),
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "what's in this"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,'/9j/4AAQSk'"},
                    },
                ],
            },
            AIMessage(
                "",
                tool_calls=[
                    {
                        "name": "analyze",
                        "args": {"baz": "buz"},
                        "id": "1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage("foobar", tool_call_id="1", name="bar"),
            {"role": "assistant", "content": "that's nice"},
        ]
        oai_messages = convert_to_openai_messages(messages)
        # -> [
        #   {'role': 'system', 'content': 'foo'},
        #   {'role': 'user', 'content': [{'type': 'text', 'text': 'what's in this'}, {'type': 'image_url', 'image_url': {'url': "data:image/png;base64,'/9j/4AAQSk'"}}]},
        #   {'role': 'assistant', 'tool_calls': [{'type': 'function', 'id': '1','function': {'name': 'analyze', 'arguments': '{"baz": "buz"}'}}], 'content': ''},
        #   {'role': 'tool', 'name': 'bar', 'content': 'foobar'},
        #   {'role': 'assistant', 'content': 'that's nice'}
        # ]
        ```

    !!! version-added "Added in `langchain-core` 0.3.11"

    """  # noqa: E501
    if text_format not in {"string", "block"}:
        err = f"Unrecognized {text_format=}, expected one of 'string' or 'block'."
        raise ValueError(err)

    oai_messages: list[dict] = []

    if is_single := isinstance(messages, (BaseMessage, dict, str)):
        messages = [messages]

    messages = convert_to_messages(messages)

    for i, message in enumerate(messages):
        oai_msg: dict = {"role": _get_message_openai_role(message)}
        tool_messages: list = []
        content: str | list[dict]

        if message.name:
            oai_msg["name"] = message.name
        if isinstance(message, AIMessage) and message.tool_calls:
            oai_msg["tool_calls"] = _convert_to_openai_tool_calls(message.tool_calls)
        if message.additional_kwargs.get("refusal"):
            oai_msg["refusal"] = message.additional_kwargs["refusal"]
        if isinstance(message, ToolMessage):
            oai_msg["tool_call_id"] = message.tool_call_id
        if include_id and message.id:
            oai_msg["id"] = message.id

        if not message.content:
            content = "" if text_format == "string" else []
        elif isinstance(message.content, str):
            if text_format == "string":
                content = message.content
            else:
                content = [{"type": "text", "text": message.content}]
        elif text_format == "string" and all(
            isinstance(block, str) or block.get("type") == "text"
            for block in message.content
        ):
            content = "\n".join(
                block if isinstance(block, str) else block["text"]
                for block in message.content
            )
        else:
            content = []
            for j, block in enumerate(message.content):
                # OpenAI format
                if isinstance(block, str):
                    content.append({"type": "text", "text": block})
                elif block.get("type") == "text":
                    if missing := [k for k in ("text",) if k not in block]:
                        err = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': 'text' "
                            f"but is missing expected key(s) "
                            f"{missing}. Full content block:\n\n{block}"
                        )
                        raise ValueError(err)
                    content.append({"type": block["type"], "text": block["text"]})
                elif block.get("type") == "image_url":
                    if missing := [k for k in ("image_url",) if k not in block]:
                        err = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': 'image_url' "
                            f"but is missing expected key(s) "
                            f"{missing}. Full content block:\n\n{block}"
                        )
                        raise ValueError(err)
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": block["image_url"],
                        }
                    )
                # Standard multi-modal content block
                elif is_data_content_block(block):
                    formatted_block = convert_to_openai_data_block(block)
                    if (
                        formatted_block.get("type") == "file"
                        and "file" in formatted_block
                        and "filename" not in formatted_block["file"]
                    ):
                        logger.info("Generating a fallback filename.")
                        formatted_block["file"]["filename"] = "LC_AUTOGENERATED"
                    content.append(formatted_block)
                # Anthropic and Bedrock converse format
                elif (block.get("type") == "image") or "image" in block:
                    # Anthropic
                    if source := block.get("source"):
                        if missing := [
                            k for k in ("media_type", "type", "data") if k not in source
                        ]:
                            err = (
                                f"Unrecognized content block at "
                                f"messages[{i}].content[{j}] has 'type': 'image' "
                                f"but 'source' is missing expected key(s) "
                                f"{missing}. Full content block:\n\n{block}"
                            )
                            raise ValueError(err)
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:{source['media_type']};"
                                        f"{source['type']},{source['data']}"
                                    )
                                },
                            }
                        )
                    # Bedrock converse
                    elif image := block.get("image"):
                        if missing := [
                            k for k in ("source", "format") if k not in image
                        ]:
                            err = (
                                f"Unrecognized content block at "
                                f"messages[{i}].content[{j}] has key 'image', "
                                f"but 'image' is missing expected key(s) "
                                f"{missing}. Full content block:\n\n{block}"
                            )
                            raise ValueError(err)
                        b64_image = _bytes_to_b64_str(image["source"]["bytes"])
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:image/{image['format']};base64,{b64_image}"
                                    )
                                },
                            }
                        )
                    else:
                        err = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': 'image' "
                            f"but does not have a 'source' or 'image' key. Full "
                            f"content block:\n\n{block}"
                        )
                        raise ValueError(err)
                # OpenAI file format
                elif (
                    block.get("type") == "file"
                    and isinstance(block.get("file"), dict)
                    and isinstance(block.get("file", {}).get("file_data"), str)
                ):
                    if block.get("file", {}).get("filename") is None:
                        logger.info("Generating a fallback filename.")
                        block["file"]["filename"] = "LC_AUTOGENERATED"
                    content.append(block)
                # OpenAI audio format
                elif (
                    block.get("type") == "input_audio"
                    and isinstance(block.get("input_audio"), dict)
                    and isinstance(block.get("input_audio", {}).get("data"), str)
                    and isinstance(block.get("input_audio", {}).get("format"), str)
                ):
                    content.append(block)
                elif block.get("type") == "tool_use":
                    if missing := [
                        k for k in ("id", "name", "input") if k not in block
                    ]:
                        err = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': "
                            f"'tool_use', but is missing expected key(s) "
                            f"{missing}. Full content block:\n\n{block}"
                        )
                        raise ValueError(err)
                    if not any(
                        tool_call["id"] == block["id"]
                        for tool_call in cast("AIMessage", message).tool_calls
                    ):
                        oai_msg["tool_calls"] = oai_msg.get("tool_calls", [])
                        oai_msg["tool_calls"].append(
                            {
                                "type": "function",
                                "id": block["id"],
                                "function": {
                                    "name": block["name"],
                                    "arguments": json.dumps(
                                        block["input"], ensure_ascii=False
                                    ),
                                },
                            }
                        )
                elif block.get("type") == "function_call":  # OpenAI Responses
                    if not any(
                        tool_call["id"] == block.get("call_id")
                        for tool_call in cast("AIMessage", message).tool_calls
                    ):
                        if missing := [
                            k
                            for k in ("call_id", "name", "arguments")
                            if k not in block
                        ]:
                            err = (
                                f"Unrecognized content block at "
                                f"messages[{i}].content[{j}] has 'type': "
                                f"'tool_use', but is missing expected key(s) "
                                f"{missing}. Full content block:\n\n{block}"
                            )
                            raise ValueError(err)
                        oai_msg["tool_calls"] = oai_msg.get("tool_calls", [])
                        oai_msg["tool_calls"].append(
                            {
                                "type": "function",
                                "id": block.get("call_id"),
                                "function": {
                                    "name": block.get("name"),
                                    "arguments": block.get("arguments"),
                                },
                            }
                        )
                    if pass_through_unknown_blocks:
                        content.append(block)
                elif block.get("type") == "tool_result":
                    if missing := [
                        k for k in ("content", "tool_use_id") if k not in block
                    ]:
                        msg = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': "
                            f"'tool_result', but is missing expected key(s) "
                            f"{missing}. Full content block:\n\n{block}"
                        )
                        raise ValueError(msg)
                    tool_message = ToolMessage(
                        block["content"],
                        tool_call_id=block["tool_use_id"],
                        status="error" if block.get("is_error") else "success",
                    )
                    # Recurse to make sure tool message contents are OpenAI format.
                    tool_messages.extend(
                        convert_to_openai_messages(
                            [tool_message], text_format=text_format
                        )
                    )
                elif (block.get("type") == "json") or "json" in block:
                    if "json" not in block:
                        msg = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': 'json' "
                            f"but does not have a 'json' key. Full "
                            f"content block:\n\n{block}"
                        )
                        raise ValueError(msg)
                    content.append(
                        {
                            "type": "text",
                            "text": json.dumps(block["json"]),
                        }
                    )
                elif (block.get("type") == "guard_content") or "guard_content" in block:
                    if (
                        "guard_content" not in block
                        or "text" not in block["guard_content"]
                    ):
                        msg = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': "
                            f"'guard_content' but does not have a "
                            f"messages[{i}].content[{j}]['guard_content']['text'] "
                            f"key. Full content block:\n\n{block}"
                        )
                        raise ValueError(msg)
                    text = block["guard_content"]["text"]
                    if isinstance(text, dict):
                        text = text["text"]
                    content.append({"type": "text", "text": text})
                # VertexAI format
                elif block.get("type") == "media":
                    if missing := [k for k in ("mime_type", "data") if k not in block]:
                        err = (
                            f"Unrecognized content block at "
                            f"messages[{i}].content[{j}] has 'type': "
                            f"'media' but does not have key(s) {missing}. Full "
                            f"content block:\n\n{block}"
                        )
                        raise ValueError(err)
                    if "image" not in block["mime_type"]:
                        err = (
                            f"OpenAI messages can only support text and image data."
                            f" Received content block with media of type:"
                            f" {block['mime_type']}"
                        )
                        raise ValueError(err)
                    b64_image = _bytes_to_b64_str(block["data"])
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (f"data:{block['mime_type']};base64,{b64_image}")
                            },
                        }
                    )
                elif (
                    block.get("type") in {"thinking", "reasoning"}
                    or pass_through_unknown_blocks
                ):
                    content.append(block)
                else:
                    err = (
                        f"Unrecognized content block at "
                        f"messages[{i}].content[{j}] does not match OpenAI, "
                        f"Anthropic, Bedrock Converse, or VertexAI format. Full "
                        f"content block:\n\n{block}"
                    )
                    raise ValueError(err)
            if text_format == "string" and not any(
                block["type"] != "text" for block in content
            ):
                content = "\n".join(block["text"] for block in content)
        oai_msg["content"] = content
        if message.content and not oai_msg["content"] and tool_messages:
            oai_messages.extend(tool_messages)
        else:
            oai_messages.extend([oai_msg, *tool_messages])

    if is_single:
        return oai_messages[0]
    return oai_messages