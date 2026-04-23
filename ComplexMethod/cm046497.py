def _normalise_responses_input(payload: ResponsesRequest) -> list:
    """Convert a ResponsesRequest into a list of ChatMessage for the completions backend."""
    messages = []

    # System / developer instructions
    if payload.instructions:
        messages.append(ChatMessage(role = "system", content = payload.instructions))

    # Simple string input
    if isinstance(payload.input, str):
        if payload.input:
            messages.append(ChatMessage(role = "user", content = payload.input))
        return messages

    # List of ResponsesInputMessage
    for msg in payload.input:
        role = "system" if msg.role == "developer" else msg.role

        if isinstance(msg.content, str):
            messages.append(ChatMessage(role = role, content = msg.content))
        else:
            # Convert Responses content parts -> Chat content parts
            parts = []
            for part in msg.content:
                if isinstance(part, ResponsesInputTextPart):
                    parts.append(TextContentPart(type = "text", text = part.text))
                elif isinstance(part, ResponsesInputImagePart):
                    parts.append(
                        ImageContentPart(
                            type = "image_url",
                            image_url = ImageUrl(url = part.image_url, detail = part.detail),
                        )
                    )
            messages.append(ChatMessage(role = role, content = parts if parts else ""))

    return messages