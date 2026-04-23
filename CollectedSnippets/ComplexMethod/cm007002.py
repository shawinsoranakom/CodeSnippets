def _extract_message_text(self) -> str:
        """Extract text content from Message input(s)."""
        if isinstance(self.data, Message):
            return self.data.text or ""

        texts = [msg.text or "" for msg in self.data if isinstance(msg, Message)]
        return "\n\n".join(texts) if len(texts) > 1 else (texts[0] if texts else "")