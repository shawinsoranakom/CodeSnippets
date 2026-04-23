async def get_messages(self) -> List[LLMMessage]:
        """Get at most `token_limit` tokens in recent messages. If the token limit is not
        provided, then return as many messages as the remaining token allowed by the model client."""
        messages = list(self._messages)
        if self._token_limit is None:
            remaining_tokens = self._model_client.remaining_tokens(messages, tools=self._tool_schema)
            while remaining_tokens < 0 and len(messages) > 0:
                middle_index = len(messages) // 2
                messages.pop(middle_index)
                remaining_tokens = self._model_client.remaining_tokens(messages, tools=self._tool_schema)
        else:
            token_count = self._model_client.count_tokens(messages, tools=self._tool_schema)
            while token_count > self._token_limit and len(messages) > 0:
                middle_index = len(messages) // 2
                messages.pop(middle_index)
                token_count = self._model_client.count_tokens(messages, tools=self._tool_schema)
        if messages and isinstance(messages[0], FunctionExecutionResultMessage):
            # Handle the first message is a function call result message.
            # Remove the first message from the list.
            messages = messages[1:]
        return messages