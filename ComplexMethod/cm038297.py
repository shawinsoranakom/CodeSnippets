def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        # Quick check to avoid unnecessary processing
        if self.tool_call_prefix not in model_output:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        # Check if both think start and end tokens are present
        if (
            self.think_start_token in model_output
            and self.think_end_token in model_output
        ):
            # Find the position of think end token
            think_end_index = model_output.find(self.think_end_token) + len(
                self.think_end_token
            )
            # Extract content after think end token
            result_content = model_output[think_end_index:]
            thinking_content = model_output[:think_end_index]
        else:
            thinking_content = ""
            result_content = model_output

        try:
            function_calls = self._get_function_calls(result_content)
            if len(function_calls) == 0:
                return ExtractedToolCallInformation(
                    tools_called=False, tool_calls=[], content=model_output
                )

            tool_calls = [
                self._parse_xml_function_call(function_call_str, self.tools)
                for function_call_str in function_calls
            ]

            # Populate prev_tool_call_arr for serving layer to set finish_reason
            self.prev_tool_call_arr.clear()  # Clear previous calls
            for tool_call in tool_calls:
                if tool_call:
                    self.prev_tool_call_arr.append(
                        {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        }
                    )

            # Extract content before tool calls
            tool_call_start_index = result_content.find(self.tool_call_start_token)
            tool_call_start_index = (
                tool_call_start_index
                if tool_call_start_index >= 0
                else result_content.find(self.tool_call_prefix)
            )
            content = thinking_content + result_content[:tool_call_start_index]

            return ExtractedToolCallInformation(
                tools_called=(len(tool_calls) > 0),
                tool_calls=tool_calls,
                content=content if content else None,
            )

        except Exception:
            logger.exception("Error in extracting tool call from response.")
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )