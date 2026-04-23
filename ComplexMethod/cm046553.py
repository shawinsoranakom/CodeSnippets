def _normalize_anthropic_openai_images(
    openai_messages: list[dict], is_vision: bool
) -> bool:
    """Enforce the vision guard on translated Anthropic messages and
    normalize any ``image_url`` parts with base64 data URLs to PNG.

    llama-server's stb_image only handles a few formats (JPEG/PNG/BMP/…);
    Anthropic clients commonly send JPEG or WebP, and Claude Code sends
    WebP. Re-encoding everything to PNG mirrors the behavior of
    `_openai_messages_for_passthrough` / the GGUF branch of
    `/v1/chat/completions` so the two endpoints agree.

    Mutates ``openai_messages`` in place. Returns ``True`` when any
    image part was seen (so the caller can skip a second scan). Raises
    HTTPException(400) when images are present but the active model is
    not a vision model, or when an image cannot be decoded.
    """
    from PIL import Image

    has_image = False
    for msg in openai_messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if part.get("type") != "image_url":
                continue

            has_image = True
            if not is_vision:
                raise HTTPException(
                    status_code = 400,
                    detail = "Image provided but current GGUF model does not support vision.",
                )

            url = (part.get("image_url") or {}).get("url", "")
            if not url.startswith("data:"):
                # Remote URLs are forwarded as-is; llama-server will
                # fetch (or fail) per its own support matrix.
                continue

            try:
                _, b64data = url.split(",", 1)
                raw = base64.b64decode(b64data)
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format = "PNG")
                png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            except Exception as e:
                raise HTTPException(
                    status_code = 400,
                    detail = f"Failed to process image: {e}",
                )
            part["image_url"] = {"url": f"data:image/png;base64,{png_b64}"}

    return has_image