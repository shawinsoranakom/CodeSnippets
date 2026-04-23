def get_buffer_string(
    messages: Sequence[BaseMessage],
    human_prefix: str = "Human",
    ai_prefix: str = "AI",
    *,
    system_prefix: str = "System",
    function_prefix: str = "Function",
    tool_prefix: str = "Tool",
    message_separator: str = "\n",
    format: Literal["prefix", "xml"] = "prefix",  # noqa: A002
) -> str:
    r"""Convert a sequence of messages to strings and concatenate them into one string.

    Args:
        messages: Messages to be converted to strings.
        human_prefix: The prefix to prepend to contents of `HumanMessage`s.
        ai_prefix: The prefix to prepend to contents of `AIMessage`.
        system_prefix: The prefix to prepend to contents of `SystemMessage`s.
        function_prefix: The prefix to prepend to contents of `FunctionMessage`s.
        tool_prefix: The prefix to prepend to contents of `ToolMessage`s.
        message_separator: The separator to use between messages.
        format: The output format. `'prefix'` uses `Role: content` format (default).

            `'xml'` uses XML-style `<message type='role'>` format with proper character
            escaping, which is useful when message content may contain role-like
            prefixes that could cause ambiguity.

    Returns:
        A single string concatenation of all input messages.

    Raises:
        ValueError: If an unsupported message type is encountered.

    !!! warning

        If a message is an `AIMessage` and contains both tool calls under `tool_calls`
        and a function call under `additional_kwargs["function_call"]`, only the tool
        calls will be appended to the string representation.

    !!! note "XML format"

        When using `format='xml'`:

        - All messages use uniform `<message type="role">content</message>` format.
        - The `type` attribute uses `human_prefix` (lowercased) for `HumanMessage`,
            `ai_prefix` (lowercased) for `AIMessage`, `system_prefix` (lowercased)
            for `SystemMessage`, `function_prefix` (lowercased) for `FunctionMessage`,
            `tool_prefix` (lowercased) for `ToolMessage`, and the original role
            (unchanged) for `ChatMessage`.
        - Message content is escaped using `xml.sax.saxutils.escape()`.
        - Attribute values are escaped using `xml.sax.saxutils.quoteattr()`.
        - AI messages with tool calls use nested structure with `<content>` and
            `<tool_call>` elements.
        - For multi-modal content (list of content blocks), supported block types
            are: `text`, `reasoning`, `image` (URL/file_id only), `image_url`
            (OpenAI-style, URL only), `audio` (URL/file_id only), `video` (URL/file_id
            only), `text-plain`, `server_tool_call`, and `server_tool_result`.
        - Content blocks with base64-encoded data are skipped (including blocks
            with `base64` field or `data:` URLs).
        - Unknown block types are skipped.
        - Plain text document content (`text-plain`), server tool call arguments,
            and server tool result outputs are truncated to 500 characters.

    Example:
        Default prefix format:

        ```python
        from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string

        messages = [
            HumanMessage(content="Hi, how are you?"),
            AIMessage(content="Good, how are you?"),
        ]
        get_buffer_string(messages)
        # -> "Human: Hi, how are you?\nAI: Good, how are you?"
        ```

        XML format (useful when content contains role-like prefixes):

        ```python
        messages = [
            HumanMessage(content="Example: Human: some text"),
            AIMessage(content="I see the example."),
        ]
        get_buffer_string(messages, format="xml")
        # -> '<message type="human">Example: Human: some text</message>\\n'
        # -> '<message type="ai">I see the example.</message>'
        ```

        XML format with special characters (automatically escaped):

        ```python
        messages = [
            HumanMessage(content="Is 5 < 10 & 10 > 5?"),
        ]
        get_buffer_string(messages, format="xml")
        # -> '<message type="human">Is 5 &lt; 10 &amp; 10 &gt; 5?</message>'
        ```

        XML format with tool calls:

        ```python
        messages = [
            AIMessage(
                content="I'll search for that.",
                tool_calls=[
                    {"id": "call_123", "name": "search", "args": {"query": "weather"}}
                ],
            ),
        ]
        get_buffer_string(messages, format="xml")
        # -> '<message type="ai">\\n'
        # -> '  <content>I\\'ll search for that.</content>\\n'
        # -> '  <tool_call id="call_123" name="search">'
        # -> '{"query": "weather"}</tool_call>\\n'
        # -> '</message>'
        ```
    """
    if format not in {"prefix", "xml"}:
        msg = (
            f"Unrecognized format={format!r}. Supported formats are 'prefix' and 'xml'."
        )
        raise ValueError(msg)

    string_messages = []
    for m in messages:
        if isinstance(m, HumanMessage):
            role = human_prefix
        elif isinstance(m, AIMessage):
            role = ai_prefix
        elif isinstance(m, SystemMessage):
            role = system_prefix
        elif isinstance(m, FunctionMessage):
            role = function_prefix
        elif isinstance(m, ToolMessage):
            role = tool_prefix
        elif isinstance(m, ChatMessage):
            role = m.role
        else:
            msg = f"Got unsupported message type: {m}"
            raise ValueError(msg)  # noqa: TRY004

        if format == "xml":
            msg_type = _get_message_type_str(
                m, human_prefix, ai_prefix, system_prefix, function_prefix, tool_prefix
            )

            # Format content blocks
            if isinstance(m.content, str):
                content_parts = [escape(m.content)] if m.content else []
            else:
                # List of content blocks
                content_parts = []
                for block in m.content:
                    if isinstance(block, str):
                        if block:
                            content_parts.append(escape(block))
                    else:
                        formatted = _format_content_block_xml(block)
                        if formatted:
                            content_parts.append(formatted)

            # Check if this is an AIMessage with tool calls
            has_tool_calls = isinstance(m, AIMessage) and m.tool_calls
            has_function_call = (
                isinstance(m, AIMessage)
                and not m.tool_calls
                and "function_call" in m.additional_kwargs
            )

            if has_tool_calls or has_function_call:
                # Use nested structure for AI messages with tool calls
                # Type narrowing: at this point m is AIMessage (verified above)
                ai_msg = cast("AIMessage", m)
                parts = [f"<message type={quoteattr(msg_type)}>"]
                if content_parts:
                    parts.append(f"  <content>{' '.join(content_parts)}</content>")

                if has_tool_calls:
                    for tc in ai_msg.tool_calls:
                        tc_id = quoteattr(str(tc.get("id") or ""))
                        tc_name = quoteattr(str(tc.get("name") or ""))
                        tc_args = escape(
                            json.dumps(tc.get("args", {}), ensure_ascii=False)
                        )
                        parts.append(
                            f"  <tool_call id={tc_id} name={tc_name}>"
                            f"{tc_args}</tool_call>"
                        )
                elif has_function_call:
                    fc = ai_msg.additional_kwargs["function_call"]
                    fc_name = quoteattr(str(fc.get("name") or ""))
                    fc_args = escape(str(fc.get("arguments") or "{}"))
                    parts.append(
                        f"  <function_call name={fc_name}>{fc_args}</function_call>"
                    )

                parts.append("</message>")
                message = "\n".join(parts)
            else:
                # Simple structure for messages without tool calls
                joined_content = " ".join(content_parts)
                message = (
                    f"<message type={quoteattr(msg_type)}>{joined_content}</message>"
                )
        else:  # format == "prefix"
            content = m.text
            message = f"{role}: {content}"
            tool_info = ""
            if isinstance(m, AIMessage):
                if m.tool_calls:
                    tool_info = str(m.tool_calls)
                elif "function_call" in m.additional_kwargs:
                    # Legacy behavior assumes only one function call per message
                    tool_info = str(m.additional_kwargs["function_call"])
            if tool_info:
                message += tool_info  # Preserve original behavior

        string_messages.append(message)

    return message_separator.join(string_messages)