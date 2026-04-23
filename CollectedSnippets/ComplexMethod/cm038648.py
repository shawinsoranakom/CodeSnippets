def parser_state_to_response_output(
    parser: StreamableParser,
) -> list[ResponseOutputItem]:
    """Extract in-progress response items from incomplete parser state.

    Called when the parser has buffered content that hasn't formed a
    complete message yet (e.g., generation was cut short).
    """
    if not parser.current_content:
        return []
    if parser.current_role != Role.ASSISTANT:
        return []
    current_recipient = parser.current_recipient
    if current_recipient is not None and current_recipient.startswith("browser."):
        return []

    if current_recipient and parser.current_channel in ("commentary", "analysis"):
        if current_recipient.startswith("functions."):
            rid = random_uuid()
            return [
                ResponseFunctionToolCall(
                    arguments=parser.current_content,
                    call_id=f"call_{rid}",
                    type="function_call",
                    name=current_recipient.split(".")[-1],
                    id=f"fc_{rid}",
                    status="in_progress",
                )
            ]
        # Built-in MCP tools (python, browser, container)
        elif current_recipient in BUILTIN_TOOL_TO_MCP_SERVER_LABEL:
            return [
                ResponseReasoningItem(
                    id=f"rs_{random_uuid()}",
                    summary=[],
                    type="reasoning",
                    content=[
                        ResponseReasoningTextContent(
                            text=parser.current_content, type="reasoning_text"
                        )
                    ],
                    status=None,
                )
            ]
        # All other recipients are MCP calls
        else:
            rid = random_uuid()
            server_label, tool_name = _parse_mcp_recipient(current_recipient)
            return [
                McpCall(
                    arguments=parser.current_content,
                    type="mcp_call",
                    name=tool_name,
                    server_label=server_label,
                    id=f"mcp_{rid}",
                    status="in_progress",
                )
            ]

    if parser.current_channel == "commentary":
        # Per Harmony format, preambles (commentary with no recipient) are
        # intended to be shown to end-users, unlike analysis channel content.
        output_text = ResponseOutputText(
            text=parser.current_content,
            annotations=[],
            type="output_text",
            logprobs=None,
        )
        return [
            ResponseOutputMessage(
                id=f"msg_{random_uuid()}",
                content=[output_text],
                role="assistant",
                status="incomplete",
                type="message",
            )
        ]

    if parser.current_channel == "analysis":
        return [
            ResponseReasoningItem(
                id=f"rs_{random_uuid()}",
                summary=[],
                type="reasoning",
                content=[
                    ResponseReasoningTextContent(
                        text=parser.current_content, type="reasoning_text"
                    )
                ],
                status=None,
            )
        ]

    if parser.current_channel == "final":
        output_text = ResponseOutputText(
            text=parser.current_content,
            annotations=[],  # TODO
            type="output_text",
            logprobs=None,  # TODO
        )
        text_item = ResponseOutputMessage(
            id=f"msg_{random_uuid()}",
            content=[output_text],
            role="assistant",
            # if the parser still has messages (ie if the generator got cut
            # abruptly), this should be incomplete
            status="incomplete",
            type="message",
        )
        return [text_item]

    return []