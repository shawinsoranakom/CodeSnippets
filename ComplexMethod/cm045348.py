async def get_messages(self) -> List[LLMMessage]:
        """Get at most `head_size` recent messages and `tail_size` oldest messages."""
        head_messages = self._messages[: self._head_size]
        # Handle the last message is a function call message.
        if (
            head_messages
            and isinstance(head_messages[-1], AssistantMessage)
            and isinstance(head_messages[-1].content, list)
            and all(isinstance(item, FunctionCall) for item in head_messages[-1].content)
        ):
            # Remove the last message from the head.
            head_messages = head_messages[:-1]

        tail_messages = self._messages[-self._tail_size :]
        # Handle the first message is a function call result message.
        if tail_messages and isinstance(tail_messages[0], FunctionExecutionResultMessage):
            # Remove the first message from the tail.
            tail_messages = tail_messages[1:]

        num_skipped = len(self._messages) - self._head_size - self._tail_size
        if num_skipped <= 0:
            # If there are not enough messages to fill the head and tail,
            # return all messages.
            return self._messages

        placeholder_messages = [UserMessage(content=f"Skipped {num_skipped} messages.", source="System")]
        return head_messages + placeholder_messages + tail_messages