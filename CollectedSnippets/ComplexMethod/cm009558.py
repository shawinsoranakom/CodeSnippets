def filter_messages(
    messages: Iterable[MessageLikeRepresentation] | PromptValue,
    *,
    include_names: Sequence[str] | None = None,
    exclude_names: Sequence[str] | None = None,
    include_types: Sequence[str | type[BaseMessage]] | None = None,
    exclude_types: Sequence[str | type[BaseMessage]] | None = None,
    include_ids: Sequence[str] | None = None,
    exclude_ids: Sequence[str] | None = None,
    exclude_tool_calls: Sequence[str] | bool | None = None,
) -> list[BaseMessage]:
    """Filter messages based on `name`, `type` or `id`.

    Args:
        messages: Sequence Message-like objects to filter.
        include_names: Message names to include.
        exclude_names: Messages names to exclude.
        include_types: Message types to include. Can be specified as string names
            (e.g. `'system'`, `'human'`, `'ai'`, ...) or as `BaseMessage`
            classes (e.g. `SystemMessage`, `HumanMessage`, `AIMessage`, ...).

        exclude_types: Message types to exclude. Can be specified as string names
            (e.g. `'system'`, `'human'`, `'ai'`, ...) or as `BaseMessage`
            classes (e.g. `SystemMessage`, `HumanMessage`, `AIMessage`, ...).

        include_ids: Message IDs to include.
        exclude_ids: Message IDs to exclude.
        exclude_tool_calls: Tool call IDs to exclude.
            Can be one of the following:
            - `True`: All `AIMessage` objects with tool calls and all `ToolMessage`
                objects will be excluded.
            - a sequence of tool call IDs to exclude:
                - `ToolMessage` objects with the corresponding tool call ID will be
                    excluded.
                - The `tool_calls` in the AIMessage will be updated to exclude
                    matching tool calls. If all `tool_calls` are filtered from an
                    AIMessage, the whole message is excluded.

    Returns:
        A list of Messages that meets at least one of the `incl_*` conditions and none
        of the `excl_*` conditions. If not `incl_*` conditions are specified then
        anything that is not explicitly excluded will be included.

    Raises:
        ValueError: If two incompatible arguments are provided.

    Example:
        ```python
        from langchain_core.messages import (
            filter_messages,
            AIMessage,
            HumanMessage,
            SystemMessage,
        )

        messages = [
            SystemMessage("you're a good assistant."),
            HumanMessage("what's your name", id="foo", name="example_user"),
            AIMessage("steve-o", id="bar", name="example_assistant"),
            HumanMessage(
                "what's your favorite color",
                id="baz",
            ),
            AIMessage(
                "silicon blue",
                id="blah",
            ),
        ]

        filter_messages(
            messages,
            include_names=("example_user", "example_assistant"),
            include_types=("system",),
            exclude_ids=("bar",),
        )
        ```

        ```python
        [
            SystemMessage("you're a good assistant."),
            HumanMessage("what's your name", id="foo", name="example_user"),
        ]
        ```
    """
    messages = convert_to_messages(messages)
    filtered: list[BaseMessage] = []
    for msg in messages:
        if (
            (exclude_names and msg.name in exclude_names)
            or (exclude_types and _is_message_type(msg, exclude_types))
            or (exclude_ids and msg.id in exclude_ids)
        ):
            continue

        if exclude_tool_calls is True and (
            (isinstance(msg, AIMessage) and msg.tool_calls)
            or isinstance(msg, ToolMessage)
        ):
            continue

        new_msg = msg
        if isinstance(exclude_tool_calls, (list, tuple, set)):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                tool_calls = [
                    tool_call
                    for tool_call in msg.tool_calls
                    if tool_call["id"] not in exclude_tool_calls
                ]
                if not tool_calls:
                    continue

                content = msg.content
                # handle Anthropic content blocks
                if isinstance(msg.content, list):
                    content = [
                        content_block
                        for content_block in msg.content
                        if (
                            not isinstance(content_block, dict)
                            or content_block.get("type") != "tool_use"
                            or content_block.get("id") not in exclude_tool_calls
                        )
                    ]

                new_msg = msg.model_copy(
                    update={"tool_calls": tool_calls, "content": content}
                )
            elif (
                isinstance(msg, ToolMessage) and msg.tool_call_id in exclude_tool_calls
            ):
                continue

        # default to inclusion when no inclusion criteria given.
        if (
            not (include_types or include_ids or include_names)
            or (include_names and new_msg.name in include_names)
            or (include_types and _is_message_type(new_msg, include_types))
            or (include_ids and new_msg.id in include_ids)
        ):
            filtered.append(new_msg)

    return filtered