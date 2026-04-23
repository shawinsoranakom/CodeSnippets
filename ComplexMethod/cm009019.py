def _extract_text_content_from_message(message: AIMessage) -> str:
        """Extract text content from an `AIMessage`.

        Args:
            message: The AI message to extract text from

        Returns:
            The extracted text content
        """
        content = message.content
        if isinstance(content, str):
            return content
        parts: list[str] = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text" and "text" in c:
                    parts.append(str(c["text"]))
                elif "content" in c and isinstance(c["content"], str):
                    parts.append(c["content"])
            else:
                parts.append(str(c))
        return "".join(parts)