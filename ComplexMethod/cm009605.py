def __add__(
        self, other: ChatGenerationChunk | list[ChatGenerationChunk]
    ) -> ChatGenerationChunk:
        """Concatenate two `ChatGenerationChunk`s.

        Args:
            other: The other `ChatGenerationChunk` or list of `ChatGenerationChunk` to
                concatenate.

        Raises:
            TypeError: If other is not a `ChatGenerationChunk` or list of
                `ChatGenerationChunk`.

        Returns:
            A new `ChatGenerationChunk` concatenated from self and other.
        """
        if isinstance(other, ChatGenerationChunk):
            generation_info = merge_dicts(
                self.generation_info or {},
                other.generation_info or {},
            )
            return ChatGenerationChunk(
                message=self.message + other.message,
                generation_info=generation_info or None,
            )
        if isinstance(other, list) and all(
            isinstance(x, ChatGenerationChunk) for x in other
        ):
            generation_info = merge_dicts(
                self.generation_info or {},
                *[chunk.generation_info for chunk in other if chunk.generation_info],
            )
            return ChatGenerationChunk(
                message=self.message + [chunk.message for chunk in other],
                generation_info=generation_info or None,
            )
        msg = f"unsupported operand type(s) for +: '{type(self)}' and '{type(other)}'"
        raise TypeError(msg)