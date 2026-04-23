def convert_last_user_msg_to_multimodal(msg: list[dict], image_data_uris: list[str], factory: str) -> None:
    if not msg or not image_data_uris:
        return

    factory_norm = (factory or "").strip().lower()

    for idx in range(len(msg) - 1, -1, -1):
        if msg[idx].get("role") != "user":
            continue

        original_content = msg[idx].get("content", "")
        text = _normalize_text_from_content(original_content)

        if factory_norm == "gemini":
            parts = []
            if text:
                parts.append({"text": text})
            for image in image_data_uris:
                mime, b64 = _parse_data_uri_or_b64(str(image), default_mime="image/png")
                parts.append({"inline_data": {"mime_type": mime, "data": b64}})
            msg[idx]["content"] = parts
            return

        if factory_norm == "anthropic":
            blocks = []
            if text:
                blocks.append({"type": "text", "text": text})
            for image in image_data_uris:
                mime, b64 = _parse_data_uri_or_b64(str(image), default_mime="image/png")
                blocks.append(
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": b64},
                    }
                )
            msg[idx]["content"] = blocks
            return

        multimodal_content = []
        if isinstance(original_content, list):
            multimodal_content = deepcopy(original_content)
        else:
            text_content = "" if original_content is None else str(original_content)
            if text_content:
                multimodal_content.append({"type": "text", "text": text_content})

        for data_uri in image_data_uris:
            image_url = data_uri
            if not isinstance(image_url, str):
                image_url = str(image_url)
            if not image_url.startswith("data:"):
                image_url = f"data:image/png;base64,{image_url}"
            multimodal_content.append({"type": "image_url", "image_url": {"url": image_url}})

        msg[idx]["content"] = multimodal_content
        return