def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        if not previous_text:
            self.parser.reset_streaming_state()
            # Reset tool call tracking arrays for new streaming session
            self.prev_tool_call_arr = []
            self.streamed_args_for_tool = []
            self.parser.set_tools(self.tools)

        # Model sometimes outputs separately causing delta_text to be empty.
        # If there were tool_calls before and all current tool_calls have ended,
        # return an empty tool_call for outer streaming output
        # to correctly output tool_call field
        if not delta_text and delta_token_ids:
            open_calls = current_text.count(
                self.parser.tool_call_start_token
            ) - current_text.count(self.parser.tool_call_end_token)
            if (
                open_calls == 0
                and self.parser.tool_call_index > 0
                or not self.parser.tool_call_index
                and current_text
            ):
                return DeltaMessage(content="")
            return None

        # Parse the delta text and get the result
        result = self.parser.parse_single_streaming_chunks(delta_text)

        # Update tool call tracking arrays based on incremental parsing results
        if result and result.tool_calls:
            for tool_call in result.tool_calls:
                if tool_call.function:
                    tool_index = (
                        tool_call.index
                        if tool_call.index is not None
                        else len(self.prev_tool_call_arr) - 1
                    )

                    # Ensure we have enough entries in our tracking arrays
                    while len(self.prev_tool_call_arr) <= tool_index:
                        self.prev_tool_call_arr.append({"name": "", "arguments": ""})
                    while len(self.streamed_args_for_tool) <= tool_index:
                        self.streamed_args_for_tool.append("")

                    # Update tool name if provided
                    if tool_call.function.name:
                        self.prev_tool_call_arr[tool_index]["name"] = (
                            tool_call.function.name
                        )

                    # Update arguments incrementally
                    if tool_call.function.arguments is not None:
                        # Concatenate the incremental arguments
                        # to the existing streamed arguments
                        self.prev_tool_call_arr[tool_index]["arguments"] += (
                            tool_call.function.arguments
                        )
                        self.streamed_args_for_tool[tool_index] += (
                            tool_call.function.arguments
                        )
        return result