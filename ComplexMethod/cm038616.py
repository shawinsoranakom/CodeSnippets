def check_system_message_content_type(cls, data):
        """Warn if system messages contain non-text content.

        According to OpenAI API spec, system messages can only be of type
        'text'. We log a warning instead of rejecting to avoid breaking
        users who intentionally send multimodal system messages.
        See: https://platform.openai.com/docs/api-reference/chat/create#chat_create-messages-system_message
        """
        if not isinstance(data, dict):
            return data
        messages = data.get("messages", [])
        for msg in messages:
            # Check if this is a system message
            if isinstance(msg, dict) and msg.get("role") == "system":
                content = msg.get("content")

                # If content is a list (multimodal format)
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            part_type = part.get("type")
                            # Infer type when 'type' field is not explicit
                            if part_type is None:
                                if "image_url" in part or "image_pil" in part:
                                    part_type = "image_url"
                                elif "image_embeds" in part:
                                    part_type = "image_embeds"
                                elif "audio_url" in part:
                                    part_type = "audio_url"
                                elif "input_audio" in part:
                                    part_type = "input_audio"
                                elif "audio_embeds" in part:
                                    part_type = "audio_embeds"
                                elif "video_url" in part:
                                    part_type = "video_url"

                            # Warn about non-text content in system messages
                            if part_type and part_type != "text":
                                logger.warning_once(
                                    "System messages should only contain text "
                                    "content according to the OpenAI API spec. "
                                    "Found content type: '%s'.",
                                    part_type,
                                )

        return data