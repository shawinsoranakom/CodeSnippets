def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        """Parse the result of an LLM call to a list of Pydantic objects.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON.

                If `True`, the output will be a JSON object containing all the keys that
                have been returned so far.

                If `False`, the output will be the full JSON object.

        Returns:
            The parsed Pydantic objects.

        Raises:
            ValueError: If the tool call arguments are not a dict.
            ValidationError: If the tool call arguments do not conform to the Pydantic
                model.
        """
        json_results = super().parse_result(result, partial=partial)
        if not json_results:
            return None if self.first_tool_only else []

        json_results = [json_results] if self.first_tool_only else json_results
        name_dict_v2: dict[str, TypeBaseModel] = {
            tool.model_config.get("title") or tool.__name__: tool
            for tool in self.tools
            if is_pydantic_v2_subclass(tool)
        }
        name_dict_v1: dict[str, TypeBaseModel] = {
            tool.__name__: tool for tool in self.tools if is_pydantic_v1_subclass(tool)
        }
        name_dict: dict[str, TypeBaseModel] = {**name_dict_v2, **name_dict_v1}
        pydantic_objects = []
        for res in json_results:
            if not isinstance(res["args"], dict):
                if partial:
                    continue
                msg = (
                    f"Tool arguments must be specified as a dict, received: "
                    f"{res['args']}"
                )
                raise ValueError(msg)

            try:
                tool = name_dict[res["type"]]
            except KeyError as e:
                available = ", ".join(name_dict.keys()) or "<no_tools>"
                msg = (
                    f"Unknown tool type: {res['type']!r}. Available tools: {available}"
                )
                raise OutputParserException(msg) from e

            try:
                pydantic_objects.append(tool(**res["args"]))
            except (ValidationError, ValueError):
                if partial:
                    continue
                has_max_tokens_stop_reason = any(
                    generation.message.response_metadata.get("stop_reason")
                    == "max_tokens"
                    for generation in result
                    if isinstance(generation, ChatGeneration)
                )
                if has_max_tokens_stop_reason:
                    logger.exception(_MAX_TOKENS_ERROR)
                raise
        if self.first_tool_only:
            return pydantic_objects[0] if pydantic_objects else None
        return pydantic_objects