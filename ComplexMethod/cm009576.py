def __add__(self, other: Any) -> BaseMessageChunk:  # type: ignore[override]
        """Message chunks support concatenation with other message chunks.

        This functionality is useful to combine message chunks yielded from
        a streaming model into a complete message.

        Args:
            other: Another message chunk to concatenate with this one.

        Returns:
            A new message chunk that is the concatenation of this message chunk
            and the other message chunk.

        Raises:
            TypeError: If the other object is not a message chunk.

        Example:
            ```txt
              AIMessageChunk(content="Hello", ...)
            + AIMessageChunk(content=" World", ...)
            = AIMessageChunk(content="Hello World", ...)
            ```
        """
        if isinstance(other, BaseMessageChunk):
            # If both are (subclasses of) BaseMessageChunk,
            # concat into a single BaseMessageChunk

            return self.__class__(
                id=self.id,
                type=self.type,
                content=merge_content(self.content, other.content),
                additional_kwargs=merge_dicts(
                    self.additional_kwargs, other.additional_kwargs
                ),
                response_metadata=merge_dicts(
                    self.response_metadata, other.response_metadata
                ),
            )
        if isinstance(other, list) and all(
            isinstance(o, BaseMessageChunk) for o in other
        ):
            content = merge_content(self.content, *(o.content for o in other))
            additional_kwargs = merge_dicts(
                self.additional_kwargs, *(o.additional_kwargs for o in other)
            )
            response_metadata = merge_dicts(
                self.response_metadata, *(o.response_metadata for o in other)
            )
            return self.__class__(  # type: ignore[call-arg]
                id=self.id,
                content=content,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
            )
        msg = (
            'unsupported operand type(s) for +: "'
            f"{self.__class__.__name__}"
            f'" and "{other.__class__.__name__}"'
        )
        raise TypeError(msg)