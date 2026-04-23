def extract_tool_calls(
        self, model_output: str, request: ChatCompletionRequest
    ) -> ExtractedToolCallInformation:
        """
        Extract tool calls from a complete model output.
        """
        try:
            # Preprocess the model output
            content, potential_tool_calls = self.preprocess_model_output(model_output)

            if not potential_tool_calls:
                return ExtractedToolCallInformation(
                    tools_called=False, tool_calls=[], content=content
                )

            # Parse the potential tool calls as JSON
            tool_calls_data = json.loads(potential_tool_calls)

            # Ensure it's an array
            if not isinstance(tool_calls_data, list):
                logger.debug("Tool calls data is not an array")
                return ExtractedToolCallInformation(
                    tools_called=False,
                    tool_calls=[],
                    content=content or model_output,
                )

            tool_calls: list[ToolCall] = []

            for idx, call in enumerate(tool_calls_data):
                if (
                    not isinstance(call, dict)
                    or "name" not in call
                    or "arguments" not in call
                ):
                    logger.debug("Invalid tool call format at index %d", idx)
                    continue

                tool_call = ToolCall(
                    id=f"call_{idx}_{random_uuid()}",
                    type="function",
                    function=FunctionCall(
                        name=call["name"],
                        arguments=(
                            json.dumps(call["arguments"])
                            if isinstance(call["arguments"], dict)
                            else call["arguments"]
                        ),
                    ),
                )
                tool_calls.append(tool_call)

            return ExtractedToolCallInformation(
                tools_called=len(tool_calls) > 0,
                tool_calls=tool_calls,
                content=content,
            )

        except Exception as e:
            logger.exception("Error extracting tool calls: %s", str(e))
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )