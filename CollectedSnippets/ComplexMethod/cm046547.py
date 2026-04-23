def _extract_content_parts(
    messages: list,
) -> tuple[str, list[dict], "Optional[str]"]:
    """
    Parse OpenAI-format messages into components the inference backend expects.

    Handles both plain-string ``content`` and multimodal content-part arrays
    (``[{type: "text", ...}, {type: "image_url", ...}]``).

    Returns:
        system_prompt:  The system message text (empty string if none provided).
        chat_messages:  Non-system messages with content flattened to strings.
        image_base64:   Base64 data of the *first* image found, or ``None``.
    """
    system_prompt = ""
    chat_messages: list[dict] = []
    first_image_b64: Optional[str] = None

    for msg in messages:
        # ── System messages → extract as system_prompt ────────
        if msg.role == "system":
            if isinstance(msg.content, str):
                system_prompt = msg.content
            elif isinstance(msg.content, list):
                # Unlikely but handle: join text parts
                system_prompt = "\n".join(
                    p.text for p in msg.content if p.type == "text"
                )
            continue

        # ── User / assistant messages ─────────────────────────
        if isinstance(msg.content, str):
            # Plain string content — pass through
            chat_messages.append({"role": msg.role, "content": msg.content})
        elif isinstance(msg.content, list):
            # Multimodal content parts
            text_parts: list[str] = []
            for part in msg.content:
                if part.type == "text":
                    text_parts.append(part.text)
                elif part.type == "image_url" and first_image_b64 is None:
                    url = part.image_url.url
                    if url.startswith("data:"):
                        # data:image/png;base64,<DATA> → extract <DATA>
                        first_image_b64 = url.split(",", 1)[1] if "," in url else None
                    else:
                        logger.warning(
                            f"Remote image URLs not yet supported: {url[:80]}..."
                        )
            combined_text = "\n".join(text_parts) if text_parts else ""
            chat_messages.append({"role": msg.role, "content": combined_text})

    return system_prompt, chat_messages, first_image_b64