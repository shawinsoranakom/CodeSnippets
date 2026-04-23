def format_prompt_preview(
    prompt_messages: List[ChatCompletionMessageParam],
    max_chars_per_message: int = 280,
) -> str:
    parts: list[str] = []
    for idx, message in enumerate(prompt_messages):
        role = str(message.get("role", "unknown")).upper()
        content = message.get("content")
        text_chunks: list[str] = []
        media_count = 0

        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type == "image_url":
                    media_count += 1
                elif item_type == "text":
                    item_text = item.get("text")
                    if isinstance(item_text, str):
                        text_chunks.append(item_text)
        else:
            text_chunks.append("" if content is None else str(content))

        preview_text = _collapse_preview_text(
            "\n".join(text_chunks), max_chars=max_chars_per_message
        )
        media_suffix = f" [{media_count} media]" if media_count else ""
        parts.append(f"{idx + 1}. {role}{media_suffix}")
        wrapped_preview = textwrap.wrap(
            preview_text, width=100, break_long_words=False, break_on_hyphens=False
        )
        if wrapped_preview:
            for line in wrapped_preview:
                parts.append(f"   {line}")
        else:
            parts.append("   (no text)")

    return "\n".join(parts)