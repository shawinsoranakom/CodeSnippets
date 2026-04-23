def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        """Parse the result of an LLM call to a list of tool calls.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON.
                If `True`, the output will be a JSON object containing
                    all the keys that have been returned so far.
                If `False`, the output will be the full JSON object.

        Raises:
            OutputParserException: If the generation is not a chat generation.

        Returns:
            The parsed tool calls.
        """
        generation = result[0]
        if not isinstance(generation, ChatGeneration):
            msg = "This output parser can only be used with a chat generation."
            raise OutputParserException(msg)
        message = generation.message
        if isinstance(message, AIMessage) and message.tool_calls:
            parsed_tool_calls = [dict(tc) for tc in message.tool_calls]
            for tool_call in parsed_tool_calls:
                if not self.return_id:
                    _ = tool_call.pop("id")
        else:
            try:
                # This exists purely for backward compatibility / cached messages
                # All new messages should use `message.tool_calls`
                raw_tool_calls = copy.deepcopy(message.additional_kwargs["tool_calls"])
            except KeyError:
                if self.first_tool_only:
                    return None
                return []
            parsed_tool_calls = parse_tool_calls(
                raw_tool_calls,
                partial=partial,
                strict=self.strict,
                return_id=self.return_id,
            )
        # For backwards compatibility
        for tc in parsed_tool_calls:
            tc["type"] = tc.pop("name")
        if self.first_tool_only:
            parsed_result = list(
                filter(lambda x: x["type"] == self.key_name, parsed_tool_calls)
            )
            single_result = (
                parsed_result[0]
                if parsed_result and parsed_result[0]["type"] == self.key_name
                else None
            )
            if self.return_id:
                return single_result
            if single_result:
                return single_result["args"]
            return None
        return (
            [res for res in parsed_tool_calls if res["type"] == self.key_name]
            if self.return_id
            else [
                res["args"] for res in parsed_tool_calls if res["type"] == self.key_name
            ]
        )