def _form_history(self, system, history, images=None):
        from google.genai import types

        contents = []
        images = images or []
        system_len = len(system) if isinstance(system, str) else 0
        history_len = len(history) if history else 0
        images_len = len(images)
        logging.info(f"[GeminiCV] _form_history called: system_len={system_len} history_len={history_len} images_len={images_len}")

        image_parts = []
        for img in images:
            try:
                image_parts.append(self._image_to_part(img))
            except Exception:
                continue

        remaining_history = history or []
        if system or remaining_history:
            parts = []
            if system:
                parts.append(types.Part(text=system))
            if remaining_history:
                first = remaining_history[0]
                parts.append(types.Part(text=first.get("content", "")))
                remaining_history = remaining_history[1:]
            parts.extend(image_parts)
            contents.append(types.Content(role="user", parts=parts))
        elif image_parts:
            contents.append(types.Content(role="user", parts=image_parts))

        role_map = {"user": "user", "assistant": "model", "system": "user"}
        for h in remaining_history:
            role = role_map.get(h.get("role"), "user")
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=h.get("content", ""))],
                )
            )

        return contents