def render_messages(messages: Messages, media: list = None) -> Iterator:
    last_is_assistant = False
    for idx, message in enumerate(messages):
        # Remove duplicate assistant messages
        if message.get("role") == "assistant":
            if last_is_assistant:
                continue
            last_is_assistant = True
        else:
            last_is_assistant = False
        # Render content parts
        if isinstance(message.get("content"), list):
            parts = [render_part(part) for part in message["content"] if part]
            if parts:
                yield {
                    **message,
                    "content": [part for part in parts if part]
                }
        else:
            # Append media to the last message
            if media is not None and idx == len(messages) - 1:
                yield {
                    **message,
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": to_input_audio(media_data, filename)
                        }
                        if is_valid_audio(media_data, filename) else {
                            "type": "image_url",
                            "image_url": {"url": to_data_uri(media_data)}
                        }
                        for media_data, filename in media
                        if media_data and is_valid_media(media_data, filename)
                    ] + ([{"type": "text", "text": message["content"]}] if isinstance(message["content"], str) else message["content"])
                }
            else:
                yield message