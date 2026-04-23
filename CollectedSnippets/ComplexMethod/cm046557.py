def _openai_messages_for_passthrough(payload) -> list[dict]:
    """Build OpenAI-format message dicts for the /v1/chat/completions
    passthrough path.

    Messages from ``payload.messages`` are dumped through Pydantic (dropping
    unset optional fields) so they are already in standard OpenAI format
    — including ``role="tool"`` tool-result messages and assistant messages
    that carry structured ``tool_calls``. Content-parts images already in
    the message list are left untouched.

    When a client uses Studio's legacy ``image_base64`` top-level field, the
    image is re-encoded to PNG (llama-server's stb_image has limited format
    support) and spliced into the last user message as an OpenAI
    ``image_url`` content part so vision + function-calling requests work
    transparently.
    """
    messages = [m.model_dump(exclude_none = True) for m in payload.messages]

    if not payload.image_base64:
        return messages

    try:
        import base64 as _b64
        from io import BytesIO as _BytesIO
        from PIL import Image as _Image

        raw = _b64.b64decode(payload.image_base64)
        img = _Image.open(_BytesIO(raw)).convert("RGB")
        buf = _BytesIO()
        img.save(buf, format = "PNG")
        png_b64 = _b64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        raise HTTPException(
            status_code = 400,
            detail = f"Failed to process image: {e}",
        )

    data_url = f"data:image/png;base64,{png_b64}"
    image_part = {"type": "image_url", "image_url": {"url": data_url}}

    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        existing = msg.get("content")
        if isinstance(existing, str):
            msg["content"] = [{"type": "text", "text": existing}, image_part]
        elif isinstance(existing, list):
            existing.append(image_part)
        else:
            msg["content"] = [image_part]
        break
    else:
        messages.append({"role": "user", "content": [image_part]})

    return messages