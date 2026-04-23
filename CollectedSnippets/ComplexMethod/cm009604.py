def set_text(self) -> Self:
        """Set the text attribute to be the contents of the message.

        Args:
            values: The values of the object.

        Returns:
            The values of the object with the text attribute set.

        Raises:
            ValueError: If the message is not a string or a list.
        """
        # Check for legacy blocks with "text" key but no "type" field.
        # Otherwise, delegate to `message.text`.
        if isinstance(self.message.content, list):
            has_legacy_blocks = any(
                isinstance(block, dict)
                and "text" in block
                and block.get("type") is None
                for block in self.message.content
            )

            if has_legacy_blocks:
                blocks = []
                for block in self.message.content:
                    if isinstance(block, str):
                        blocks.append(block)
                    elif isinstance(block, dict):
                        block_type = block.get("type")
                        if block_type == "text" or (
                            block_type is None and "text" in block
                        ):
                            blocks.append(block.get("text", ""))
                self.text = "".join(blocks)
            else:
                self.text = self.message.text
        else:
            self.text = self.message.text

        return self