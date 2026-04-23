def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        """Parse the result of an LLM call to a list of tool calls.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON.

                If `True`, the output will be a JSON object containing
                all the keys that have been returned so far.

                If `False`, the output will be the full JSON object.

        Returns:
            The parsed tool calls.

        Raises:
            OutputParserException: If the output is not valid JSON.
        """
        generation = result[0]
        if not isinstance(generation, ChatGeneration):
            msg = "This output parser can only be used with a chat generation."
            raise OutputParserException(msg)
        message = generation.message
        if isinstance(message, AIMessage) and message.tool_calls:
            tool_calls = [dict(tc) for tc in message.tool_calls]
            for tool_call in tool_calls:
                if not self.return_id:
                    _ = tool_call.pop("id")
        else:
            try:
                raw_tool_calls = copy.deepcopy(message.additional_kwargs["tool_calls"])
            except KeyError:
                return []
            tool_calls = parse_tool_calls(
                raw_tool_calls,
                partial=partial,
                strict=self.strict,
                return_id=self.return_id,
            )
        # for backwards compatibility
        for tc in tool_calls:
            tc["type"] = tc.pop("name")

        if self.first_tool_only:
            return tool_calls[0] if tool_calls else None
        return tool_calls