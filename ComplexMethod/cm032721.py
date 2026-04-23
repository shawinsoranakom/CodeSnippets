def _resolve_video_prompt(self, system, history, **kwargs):
        prompt = kwargs.get("video_prompt") or kwargs.get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            return prompt.strip()

        for h in reversed(history or []):
            if h.get("role") != "user":
                continue
            txt = self._extract_text_from_content(h.get("content"))
            if txt:
                return txt

        if isinstance(system, str) and system.strip():
            return system.strip()

        return "Please summarize this video in proper sentences."