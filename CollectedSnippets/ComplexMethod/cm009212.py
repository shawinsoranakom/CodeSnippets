def _format_messages(
    messages: Sequence[BaseMessage],
) -> tuple[str | list[dict] | None, list[dict]]:
    """Format messages for Anthropic's API."""
    system: str | list[dict] | None = None
    formatted_messages: list[dict] = []
    merged_messages = _merge_messages(messages)
    for _i, message in enumerate(merged_messages):
        if message.type == "system":
            if system is not None:
                msg = "Received multiple non-consecutive system messages."
                raise ValueError(msg)
            if isinstance(message.content, list):
                system = [
                    (
                        block
                        if isinstance(block, dict)
                        else {"type": "text", "text": block}
                    )
                    for block in message.content
                ]
            else:
                system = message.content
            continue

        role = _message_type_lookups[message.type]
        content: str | list

        if not isinstance(message.content, str):
            # parse as dict
            if not isinstance(message.content, list):
                msg = "Anthropic message content must be str or list of dicts"
                raise ValueError(
                    msg,
                )

            # populate content
            content = []
            for block in message.content:
                if isinstance(block, str):
                    content.append({"type": "text", "text": block})
                elif isinstance(block, dict):
                    if "type" not in block:
                        msg = "Dict content block must have a type key"
                        raise ValueError(msg)
                    if block["type"] in ("reasoning", "function_call") and (
                        not isinstance(message, AIMessage)
                        or message.response_metadata.get("model_provider")
                        != "anthropic"
                    ):
                        continue
                    if block["type"] == "image_url":
                        # convert format
                        source = _format_image(block["image_url"]["url"])
                        content.append({"type": "image", "source": source})
                    elif is_data_content_block(block):
                        content.append(_format_data_content_block(block))
                    elif block["type"] == "tool_use":
                        # If a tool_call with the same id as a tool_use content block
                        # exists, the tool_call is preferred.
                        if (
                            isinstance(message, AIMessage)
                            and (block["id"] in [tc["id"] for tc in message.tool_calls])
                            and not block.get("caller")
                        ):
                            overlapping = [
                                tc
                                for tc in message.tool_calls
                                if tc["id"] == block["id"]
                            ]
                            content.extend(
                                _lc_tool_calls_to_anthropic_tool_use_blocks(
                                    overlapping,
                                ),
                            )
                        else:
                            if tool_input := block.get("input"):
                                args = tool_input
                            elif "partial_json" in block:
                                try:
                                    args = json.loads(block["partial_json"] or "{}")
                                except json.JSONDecodeError:
                                    args = {}
                            else:
                                args = {}
                            tool_use_block = _AnthropicToolUse(
                                type="tool_use",
                                name=block["name"],
                                input=args,
                                id=block["id"],
                            )
                            if caller := block.get("caller"):
                                tool_use_block["caller"] = caller
                            content.append(tool_use_block)
                    elif block["type"] in ("server_tool_use", "mcp_tool_use"):
                        formatted_block = {
                            k: v
                            for k, v in block.items()
                            if k
                            in (
                                "type",
                                "id",
                                "input",
                                "name",
                                "server_name",  # for mcp_tool_use
                                "cache_control",
                            )
                        }
                        # Attempt to parse streamed output
                        if block.get("input") == {} and "partial_json" in block:
                            try:
                                input_ = json.loads(block["partial_json"])
                                if input_:
                                    formatted_block["input"] = input_
                            except json.JSONDecodeError:
                                pass
                        content.append(formatted_block)
                    elif block["type"] == "text":
                        text = block.get("text", "")
                        # Only add non-empty strings for now as empty ones are not
                        # accepted.
                        # https://github.com/anthropics/anthropic-sdk-python/issues/461
                        if text.strip():
                            formatted_block = {
                                k: v
                                for k, v in block.items()
                                if k in ("type", "text", "cache_control", "citations")
                            }
                            # Clean up citations to remove null file_id fields
                            if formatted_block.get("citations"):
                                cleaned_citations = []
                                for citation in formatted_block["citations"]:
                                    cleaned_citation = {
                                        k: v
                                        for k, v in citation.items()
                                        if not (k == "file_id" and v is None)
                                    }
                                    cleaned_citations.append(cleaned_citation)
                                formatted_block["citations"] = cleaned_citations
                            content.append(formatted_block)
                    elif block["type"] == "thinking":
                        content.append(
                            {
                                k: v
                                for k, v in block.items()
                                if k
                                in ("type", "thinking", "cache_control", "signature")
                            },
                        )
                    elif block["type"] == "redacted_thinking":
                        content.append(
                            {
                                k: v
                                for k, v in block.items()
                                if k in ("type", "cache_control", "data")
                            },
                        )
                    elif (
                        block["type"] == "tool_result"
                        and isinstance(block.get("content"), list)
                        and any(
                            isinstance(item, dict)
                            and item.get("type") == "tool_reference"
                            for item in block["content"]
                        )
                    ):
                        # Tool search results with tool_reference blocks
                        content.append(
                            {
                                k: v
                                for k, v in block.items()
                                if k
                                in (
                                    "type",
                                    "content",
                                    "tool_use_id",
                                    "cache_control",
                                )
                            },
                        )
                    elif block["type"] == "tool_result":
                        # Regular tool results that need content formatting
                        tool_content = _format_messages(
                            [HumanMessage(block["content"])],
                        )[1][0]["content"]
                        content.append({**block, "content": tool_content})
                    elif block["type"] in (
                        "code_execution_tool_result",
                        "bash_code_execution_tool_result",
                        "text_editor_code_execution_tool_result",
                        "mcp_tool_result",
                        "web_search_tool_result",
                        "web_fetch_tool_result",
                    ):
                        content.append(
                            {
                                k: v
                                for k, v in block.items()
                                if k
                                in (
                                    "type",
                                    "content",
                                    "tool_use_id",
                                    "is_error",  # for mcp_tool_result
                                    "cache_control",
                                    "retrieved_at",  # for web_fetch_tool_result
                                )
                            },
                        )
                    else:
                        content.append(block)
                else:
                    msg = (
                        f"Content blocks must be str or dict, instead was: "
                        f"{type(block)}"
                    )
                    raise ValueError(
                        msg,
                    )
        else:
            content = message.content

        # Ensure all tool_calls have a tool_use content block
        if isinstance(message, AIMessage) and message.tool_calls:
            content = content or []
            content = (
                [{"type": "text", "text": message.content}]
                if isinstance(content, str) and content
                else content
            )
            tool_use_ids = [
                cast("dict", block)["id"]
                for block in content
                if cast("dict", block)["type"] == "tool_use"
            ]
            missing_tool_calls = [
                tc for tc in message.tool_calls if tc["id"] not in tool_use_ids
            ]
            cast("list", content).extend(
                _lc_tool_calls_to_anthropic_tool_use_blocks(missing_tool_calls),
            )

        if role == "assistant" and _i == len(merged_messages) - 1:
            if isinstance(content, str):
                content = content.rstrip()
            elif (
                isinstance(content, list)
                and content
                and isinstance(content[-1], dict)
                and content[-1].get("type") == "text"
            ):
                content[-1]["text"] = content[-1]["text"].rstrip()

        if not content and role == "assistant" and _i < len(merged_messages) - 1:
            # anthropic.BadRequestError: Error code: 400: all messages must have
            # non-empty content except for the optional final assistant message
            continue
        formatted_messages.append({"role": role, "content": content})
    return system, formatted_messages