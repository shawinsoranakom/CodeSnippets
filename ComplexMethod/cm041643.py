def parse_qwen3_message(generated_text: str) -> Message:
    """Parse a message in the Qwen3 template format. Supports interleaved reasoning and tool calls.

    Args:
        generated_text (str): The generated text in the Qwen3 template format.

    Returns:
        Message: The parsed message.
    """
    pattern = re.compile(r"<(think|tool_call)>\s*(.*?)\s*</\1>\s*", re.DOTALL)
    content = []
    last_end = 0

    for match in pattern.finditer(generated_text):
        start, end = match.span()
        if start > last_end:
            text = generated_text[last_end:start].strip()
            if text:
                content.append({"type": "text", "value": text})

        tag_type = match.group(1)
        tag_value = match.group(2).strip()
        if tag_type == "think":
            content.append({"type": "reasoning", "value": tag_value.strip()})
        elif tag_type == "tool_call":
            try:
                json.loads(tag_value.strip())
            except json.JSONDecodeError:
                raise ValueError(f"Invalid tool call format: {tag_value.strip()}.")

            content.append({"type": "tool_call", "value": tag_value.strip()})

        last_end = end

    if last_end < len(generated_text):
        text = generated_text[last_end:].strip()
        if text:
            content.append({"type": "text", "value": text})

    return Message(role="assistant", content=content)