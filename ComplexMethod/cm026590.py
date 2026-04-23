def _convert_content(  # noqa: C901
    chat_content: Iterable[conversation.Content],
) -> tuple[list[MessageParam], str | None]:
    """Transform HA chat_log content into Anthropic API format."""
    messages: list[MessageParam] = []
    container_id: str | None = None

    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            external_tool = True
            if content.tool_name == "web_search":
                tool_result_block: ContentBlockParam = {
                    "type": "web_search_tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": cast(
                        WebSearchToolResultBlockParamContentParam,
                        content.tool_result["content"]
                        if "content" in content.tool_result
                        else {
                            "type": "web_search_tool_result_error",
                            "error_code": content.tool_result.get(
                                "error_code", "unavailable"
                            ),
                        },
                    ),
                }
            elif content.tool_name == "code_execution":
                tool_result_block = {
                    "type": "code_execution_tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": cast(
                        CodeExecutionToolResultBlockParamContentParam,
                        content.tool_result,
                    ),
                }
            elif content.tool_name == "bash_code_execution":
                tool_result_block = {
                    "type": "bash_code_execution_tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": cast(
                        BashCodeExecutionToolResultBlockParamContentParam,
                        content.tool_result,
                    ),
                }
            elif content.tool_name == "text_editor_code_execution":
                tool_result_block = {
                    "type": "text_editor_code_execution_tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": cast(
                        TextEditorCodeExecutionToolResultBlockParamContentParam,
                        content.tool_result,
                    ),
                }
            elif content.tool_name == "tool_search":
                tool_result_block = {
                    "type": "tool_search_tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": cast(
                        ToolSearchToolResultBlockParamContentParam,
                        content.tool_result,
                    ),
                }
            else:
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": content.tool_call_id,
                    "content": json_dumps(content.tool_result),
                }
                external_tool = False
            if not messages or messages[-1]["role"] != (
                "assistant" if external_tool else "user"
            ):
                messages.append(
                    MessageParam(
                        role="assistant" if external_tool else "user",
                        content=[tool_result_block],
                    )
                )
            elif isinstance(messages[-1]["content"], str):
                messages[-1]["content"] = [
                    TextBlockParam(type="text", text=messages[-1]["content"]),
                    tool_result_block,
                ]
            else:
                messages[-1]["content"].append(tool_result_block)  # type: ignore[attr-defined]
        elif isinstance(content, conversation.UserContent):
            # Combine consequent user messages
            if not messages or messages[-1]["role"] != "user":
                messages.append(
                    MessageParam(
                        role="user",
                        content=content.content,
                    )
                )
            elif isinstance(messages[-1]["content"], str):
                messages[-1]["content"] = [
                    TextBlockParam(type="text", text=messages[-1]["content"]),
                    TextBlockParam(type="text", text=content.content),
                ]
            else:
                messages[-1]["content"].append(  # type: ignore[attr-defined]
                    TextBlockParam(type="text", text=content.content)
                )
        elif isinstance(content, conversation.AssistantContent):
            # Combine consequent assistant messages
            if not messages or messages[-1]["role"] != "assistant":
                messages.append(
                    MessageParam(
                        role="assistant",
                        content=[],
                    )
                )
            elif isinstance(messages[-1]["content"], str):
                messages[-1]["content"] = [
                    TextBlockParam(type="text", text=messages[-1]["content"]),
                ]

            if isinstance(content.native, ContentDetails):
                if content.native.thinking_signature:
                    messages[-1]["content"].append(  # type: ignore[union-attr]
                        ThinkingBlockParam(
                            type="thinking",
                            thinking=content.thinking_content or "",
                            signature=content.native.thinking_signature,
                        )
                    )
                if content.native.redacted_thinking:
                    messages[-1]["content"].append(  # type: ignore[union-attr]
                        RedactedThinkingBlockParam(
                            type="redacted_thinking",
                            data=content.native.redacted_thinking,
                        )
                    )
                if (
                    content.native.container is not None
                    and content.native.container.expires_at > datetime.now(UTC)
                ):
                    container_id = content.native.container.id

            if content.content:
                current_index = 0
                for detail in (
                    content.native.citation_details
                    if isinstance(content.native, ContentDetails)
                    else [CitationDetails(length=len(content.content))]
                ):
                    if detail.index > current_index:
                        # Add text block for any text without citations
                        messages[-1]["content"].append(  # type: ignore[union-attr]
                            TextBlockParam(
                                type="text",
                                text=content.content[current_index : detail.index],
                            )
                        )
                    messages[-1]["content"].append(  # type: ignore[union-attr]
                        TextBlockParam(
                            type="text",
                            text=content.content[
                                detail.index : detail.index + detail.length
                            ],
                            citations=detail.citations,
                        )
                        if detail.citations
                        else TextBlockParam(
                            type="text",
                            text=content.content[
                                detail.index : detail.index + detail.length
                            ],
                        )
                    )
                    current_index = detail.index + detail.length
                if current_index < len(content.content):
                    # Add text block for any remaining text without citations
                    messages[-1]["content"].append(  # type: ignore[union-attr]
                        TextBlockParam(
                            type="text",
                            text=content.content[current_index:],
                        )
                    )

            if content.tool_calls:
                messages[-1]["content"].extend(  # type: ignore[union-attr]
                    [
                        ServerToolUseBlockParam(
                            type="server_tool_use",
                            id=tool_call.id,
                            name=cast(
                                Literal[
                                    "web_search",
                                    "code_execution",
                                    "bash_code_execution",
                                    "text_editor_code_execution",
                                    "tool_search_tool_bm25",
                                ],
                                tool_call.tool_name,
                            ),
                            input=tool_call.tool_args,
                        )
                        if tool_call.external
                        and tool_call.tool_name
                        in [
                            "web_search",
                            "code_execution",
                            "bash_code_execution",
                            "text_editor_code_execution",
                            "tool_search_tool_bm25",
                        ]
                        else ToolUseBlockParam(
                            type="tool_use",
                            id=tool_call.id,
                            name=tool_call.tool_name,
                            input=tool_call.tool_args,
                        )
                        for tool_call in content.tool_calls
                    ]
                )

            if (
                isinstance(messages[-1]["content"], list)
                and len(messages[-1]["content"]) == 1
                and messages[-1]["content"][0]["type"] == "text"
            ):
                # If there is only one text block, simplify the content to a string
                messages[-1]["content"] = messages[-1]["content"][0]["text"]
        else:
            # Note: We don't pass SystemContent here as it's passed to the API as the prompt
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unexpected_chat_log_content",
                translation_placeholders={"type": type(content).__name__},
            )

    return messages, container_id