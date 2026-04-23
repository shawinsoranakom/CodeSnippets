def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        """Parse the result of an LLM call to a JSON object.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON objects.

        Returns:
            The parsed JSON object.

        Raises:
            OutputParserException: If the output is not valid JSON.
        """
        if len(result) != 1:
            msg = f"Expected exactly one result, but got {len(result)}"
            raise OutputParserException(msg)
        generation = result[0]
        if not isinstance(generation, ChatGeneration):
            msg = "This output parser can only be used with a chat generation."
            raise OutputParserException(msg)
        message = generation.message
        try:
            function_call = message.additional_kwargs["function_call"]
        except KeyError as exc:
            if partial:
                return None
            msg = f"Could not parse function call: {exc}"
            raise OutputParserException(msg) from exc
        try:
            if partial:
                try:
                    if self.args_only:
                        return parse_partial_json(
                            function_call["arguments"], strict=self.strict
                        )
                    return {
                        **function_call,
                        "arguments": parse_partial_json(
                            function_call["arguments"], strict=self.strict
                        ),
                    }
                except json.JSONDecodeError:
                    return None
            elif self.args_only:
                try:
                    return json.loads(function_call["arguments"], strict=self.strict)
                except (json.JSONDecodeError, TypeError) as exc:
                    msg = f"Could not parse function call data: {exc}"
                    raise OutputParserException(msg) from exc
            else:
                try:
                    return {
                        **function_call,
                        "arguments": json.loads(
                            function_call["arguments"], strict=self.strict
                        ),
                    }
                except (json.JSONDecodeError, TypeError) as exc:
                    msg = f"Could not parse function call data: {exc}"
                    raise OutputParserException(msg) from exc
        except KeyError:
            return None