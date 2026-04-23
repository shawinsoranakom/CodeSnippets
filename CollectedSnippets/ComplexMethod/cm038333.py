def extract_tool_calls(
        self, model_output: str, request: ChatCompletionRequest
    ) -> ExtractedToolCallInformation:
        """
        Extract the tool calls from a complete model response.
        Only extracts JSON content and ignores any surrounding plain text.
        Supports both single JSON and multiple JSONs separated by semicolons.
        """
        # Quick check before running regex
        if not (self.bot_token in model_output or "{" in model_output):
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        # Keep track of the end index of the last parsed JSON object
        # so we don't parse inner brackets
        end_index = -1
        tool_calls: list[ToolCall] = []

        try:
            for match in self.tool_call_start_regex.finditer(
                model_output, timeout=envs.VLLM_TOOL_PARSE_REGEX_TIMEOUT_SECONDS
            ):
                start_index = match.start()
                # Skip if this brace is inside a previously parsed JSON object
                if start_index <= end_index:
                    continue

                try:
                    obj, json_end_index = self.json_decoder.raw_decode(
                        model_output[start_index:]
                    )
                    end_index = start_index + json_end_index

                    # raise KeyError if missing
                    name = obj["name"]
                    arguments_or_params = (
                        obj["arguments"] if "arguments" in obj else obj["parameters"]
                    )

                    tool_calls.append(
                        ToolCall(
                            type="function",
                            function=FunctionCall(
                                name=name,
                                # function call args are JSON but as a string
                                arguments=json.dumps(
                                    arguments_or_params, ensure_ascii=False
                                ),
                            ),
                        )
                    )
                except KeyError as e:
                    # Missing required key
                    missing_key = str(e).strip("'\"")
                    logger.exception(
                        "Couldn't extract tool call from JSON response. "
                        "Required key '%s' not present. "
                        "Returning output in content with empty tool calls.",
                        missing_key,
                    )
                    return ExtractedToolCallInformation(
                        tools_called=False, tool_calls=[], content=model_output
                    )
                except Exception:
                    # Any other error during parsing
                    logger.exception(
                        "Error in extracting tool call from response. "
                        "Returning output in content with empty tool calls"
                    )
                    return ExtractedToolCallInformation(
                        tools_called=False, tool_calls=[], content=model_output
                    )
        except TimeoutError:
            logger.warning("Regex timeout occurred when matching tool call pattern.")
            logger.debug(
                "Regex timeout occurred when matching user input: %s", model_output
            )
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        # If we have valid tool calls, return them normally
        if tool_calls:
            return ExtractedToolCallInformation(
                tools_called=True, tool_calls=tool_calls, content=None
            )

        # No valid tool calls found
        return ExtractedToolCallInformation(
            tools_called=False, tool_calls=[], content=model_output
        )