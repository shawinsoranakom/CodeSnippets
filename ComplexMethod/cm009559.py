def merge_message_runs(
    messages: Iterable[MessageLikeRepresentation] | PromptValue,
    *,
    chunk_separator: str = "\n",
) -> list[BaseMessage]:
    r"""Merge consecutive Messages of the same type.

    !!! note
        `ToolMessage` objects are not merged, as each has a distinct tool call id that
        can't be merged.

    Args:
        messages: Sequence Message-like objects to merge.
        chunk_separator: Specify the string to be inserted between message chunks.

    Returns:
        list of BaseMessages with consecutive runs of message types merged into single
        messages. By default, if two messages being merged both have string contents,
        the merged content is a concatenation of the two strings with a new-line
        separator.
        The separator inserted between message chunks can be controlled by specifying
        any string with `chunk_separator`. If at least one of the messages has a list
        of content blocks, the merged content is a list of content blocks.

    Example:
        ```python
        from langchain_core.messages import (
            merge_message_runs,
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolCall,
        )

        messages = [
            SystemMessage("you're a good assistant."),
            HumanMessage(
                "what's your favorite color",
                id="foo",
            ),
            HumanMessage(
                "wait your favorite food",
                id="bar",
            ),
            AIMessage(
                "my favorite colo",
                tool_calls=[
                    ToolCall(
                        name="blah_tool", args={"x": 2}, id="123", type="tool_call"
                    )
                ],
                id="baz",
            ),
            AIMessage(
                [{"type": "text", "text": "my favorite dish is lasagna"}],
                tool_calls=[
                    ToolCall(
                        name="blah_tool",
                        args={"x": -10},
                        id="456",
                        type="tool_call",
                    )
                ],
                id="blur",
            ),
        ]

        merge_message_runs(messages)
        ```

        ```python
        [
            SystemMessage("you're a good assistant."),
            HumanMessage(
                "what's your favorite color\\n"
                "wait your favorite food", id="foo",
            ),
            AIMessage(
                [
                    "my favorite colo",
                    {"type": "text", "text": "my favorite dish is lasagna"}
                ],
                tool_calls=[
                    ToolCall({
                        "name": "blah_tool",
                        "args": {"x": 2},
                        "id": "123",
                        "type": "tool_call"
                    }),
                    ToolCall({
                        "name": "blah_tool",
                        "args": {"x": -10},
                        "id": "456",
                        "type": "tool_call"
                    })
                ]
                id="baz"
            ),
        ]

        ```
    """
    if not messages:
        return []
    messages = convert_to_messages(messages)
    merged: list[BaseMessage] = []
    for msg in messages:
        last = merged.pop() if merged else None
        if not last:
            merged.append(msg)
        elif isinstance(msg, ToolMessage) or not isinstance(msg, last.__class__):
            merged.extend([last, msg])
        else:
            last_chunk = _msg_to_chunk(last)
            curr_chunk = _msg_to_chunk(msg)
            if curr_chunk.response_metadata:
                curr_chunk.response_metadata.clear()
            if (
                isinstance(last_chunk.content, str)
                and isinstance(curr_chunk.content, str)
                and last_chunk.content
                and curr_chunk.content
            ):
                last_chunk.content += chunk_separator
            merged.append(_chunk_to_msg(last_chunk + curr_chunk))
    return merged