def text(self) -> TextAccessor:
        """Get the text content of the message as a string.

        Can be used as both property (`message.text`) and method (`message.text()`).

        Handles both string and list content types (e.g. for content blocks). Only
        extracts blocks with `type: 'text'`; other block types are ignored.

        !!! deprecated
            As of `langchain-core` 1.0.0, calling `.text()` as a method is deprecated.
            Use `.text` as a property instead. This method will be removed in 2.0.0.

        Returns:
            The text content of the message.

        """
        if isinstance(self.content, str):
            text_value = self.content
        else:
            # Must be a list
            blocks = [
                block
                for block in self.content
                if isinstance(block, str)
                or (block.get("type") == "text" and isinstance(block.get("text"), str))
            ]
            text_value = "".join(
                block if isinstance(block, str) else block["text"] for block in blocks
            )
        return TextAccessor(text_value)