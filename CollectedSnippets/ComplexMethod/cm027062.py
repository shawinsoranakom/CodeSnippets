def _convert_content(
    content: (
        conversation.UserContent
        | conversation.AssistantContent
        | conversation.SystemContent
    ),
) -> Content:
    """Convert HA content to Google content."""
    if content.role != "assistant":
        return Content(
            role=content.role,
            parts=[Part.from_text(text=content.content or "")],
        )

    # Handle the Assistant content with tool calls.
    assert type(content) is conversation.AssistantContent
    parts: list[Part] = []
    part_details: list[PartDetails] = (
        content.native.part_details
        if isinstance(content.native, ContentDetails)
        else []
    )
    details: PartDetails | None = None

    if content.content:
        index = 0
        for details in part_details:
            if details.part_type == "text":
                if index < details.index:
                    parts.append(
                        Part.from_text(text=content.content[index : details.index])
                    )
                    index = details.index
                parts.append(
                    Part.from_text(
                        text=content.content[index : index + details.length],
                    )
                )
                if details.thought_signature:
                    parts[-1].thought_signature = base64.b64decode(
                        details.thought_signature
                    )
                index += details.length
        if index < len(content.content):
            parts.append(Part.from_text(text=content.content[index:]))

    if content.thinking_content:
        index = 0
        for details in part_details:
            if details.part_type == "thought":
                if index < details.index:
                    parts.append(
                        Part.from_text(
                            text=content.thinking_content[index : details.index]
                        )
                    )
                    parts[-1].thought = True
                    index = details.index
                parts.append(
                    Part.from_text(
                        text=content.thinking_content[index : index + details.length],
                    )
                )
                parts[-1].thought = True
                if details.thought_signature:
                    parts[-1].thought_signature = base64.b64decode(
                        details.thought_signature
                    )
                index += details.length
        if index < len(content.thinking_content):
            parts.append(Part.from_text(text=content.thinking_content[index:]))
            parts[-1].thought = True

    if content.tool_calls:
        for index, tool_call in enumerate(content.tool_calls):
            parts.append(
                Part.from_function_call(
                    name=tool_call.tool_name,
                    args=_escape_decode(tool_call.tool_args),
                )
            )
            if details := next(
                (
                    d
                    for d in part_details
                    if d.part_type == "function_call" and d.index == index
                ),
                None,
            ):
                if details.thought_signature:
                    parts[-1].thought_signature = base64.b64decode(
                        details.thought_signature
                    )

    return Content(role="model", parts=parts)