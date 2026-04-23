def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        """Parse a list of candidate model Generations into a specific format.

        Args:
            result: A list of `Generation` to be parsed. The Generations are assumed
                to be different candidate outputs for a single model input.
            partial: (Not used) Whether the result is a partial result. If `True`, the
                parser may return a partial result, which may not be complete or valid.

        Returns:
            Structured output.

        """
        if not result or not isinstance(result[0], ChatGeneration):
            return None if self.first_tool_only else []
        message = cast("AIMessage", result[0].message)
        tool_calls: list = [
            dict(tc) for tc in _extract_tool_calls_from_message(message)
        ]
        if isinstance(message.content, list):
            # Map tool call id to index
            id_to_index = {
                block["id"]: i
                for i, block in enumerate(message.content)
                if isinstance(block, dict) and block["type"] == "tool_use"
            }
            tool_calls = [{**tc, "index": id_to_index[tc["id"]]} for tc in tool_calls]
        if self.pydantic_schemas:
            tool_calls = [self._pydantic_parse(tc) for tc in tool_calls]
        elif self.args_only:
            tool_calls = [tc["args"] for tc in tool_calls]
        else:
            pass

        if self.first_tool_only:
            return tool_calls[0] if tool_calls else None
        return list(tool_calls)