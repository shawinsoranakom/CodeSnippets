def _convert_single_sample(sample):
        """Convert a single ShareGPT+image sample to standard VLM format."""
        pil_image = _resolve_image(sample[image_column])
        conversation = sample[messages_column]

        new_messages = []
        for msg in conversation:
            role_raw = msg.get("from") or msg.get("role", "user")
            role = _ROLE_MAP.get(role_raw.lower(), role_raw.lower())
            text = msg.get("value") or msg.get("content") or ""

            # Split on <image> to interleave text and image content blocks
            if "<image>" in text:
                parts = text.split("<image>")
                content = []
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        content.append({"type": "text", "text": part})
                    if i < len(parts) - 1:
                        content.append({"type": "image", "image": pil_image})
                # If <image> was the entire text, content might just be the image
                if not content:
                    content.append({"type": "image", "image": pil_image})
            else:
                content = [{"type": "text", "text": text}]

            new_messages.append({"role": role, "content": content})

        return {"messages": new_messages}