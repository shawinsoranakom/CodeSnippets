def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        self.parser.reset_streaming_state()
        # Reset tool call tracking arrays for new extraction
        self.prev_tool_call_arr = []
        self.streamed_args_for_tool = []
        self.parser.set_tools(self.tools)
        result = self.parser.parse_single_streaming_chunks(model_output)
        if not result.tool_calls:
            return ExtractedToolCallInformation(
                tool_calls=[],
                tools_called=False,
                content=result.content,
            )
        else:
            tool_calls = []
            for tool_call in result.tool_calls:
                if tool_call.function and tool_call.function.name:
                    tool_calls.append(
                        ToolCall(
                            id=tool_call.id,
                            type=tool_call.type,
                            function=FunctionCall(
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            ),
                        )
                    )

                    # Update tool call tracking arrays for compatibility
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

                    # Update tool call information
                    self.prev_tool_call_arr[tool_index]["name"] = (
                        tool_call.function.name
                    )
                    self.prev_tool_call_arr[tool_index]["arguments"] = (
                        tool_call.function.arguments
                    )

                    # Update streamed arguments
                    if tool_call.function.arguments:
                        self.streamed_args_for_tool[tool_index] = (
                            tool_call.function.arguments
                        )

            return ExtractedToolCallInformation(
                tool_calls=tool_calls,
                tools_called=len(tool_calls) > 0,
                content=result.content,
            )