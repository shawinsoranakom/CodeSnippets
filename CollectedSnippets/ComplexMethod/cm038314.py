def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        """Extract tool calls from complete model output (non-streaming)."""
        # Quick check
        if self.tool_call_start_token not in model_output:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        try:
            tool_calls = []

            # Find all complete tool_call blocks
            for tool_call_match in self.tool_call_complete_regex.findall(model_output):
                # Find all invokes within this tool_call
                for invoke_match in self.invoke_complete_regex.findall(tool_call_match):
                    tool_call = self._parse_single_invoke(invoke_match, self.tools)
                    if tool_call:
                        tool_calls.append(tool_call)

            if not tool_calls:
                return ExtractedToolCallInformation(
                    tools_called=False, tool_calls=[], content=model_output
                )

            # Update prev_tool_call_arr
            self.prev_tool_call_arr.clear()
            for tool_call in tool_calls:
                self.prev_tool_call_arr.append(
                    {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    }
                )

            # Extract content before first tool call
            first_tool_idx = model_output.find(self.tool_call_start_token)
            content = model_output[:first_tool_idx] if first_tool_idx > 0 else None

            return ExtractedToolCallInformation(
                tools_called=True, tool_calls=tool_calls, content=content
            )

        except Exception:
            logger.exception("Error extracting tool calls")
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )