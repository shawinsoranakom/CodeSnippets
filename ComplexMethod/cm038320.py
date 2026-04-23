def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        """
        Extract tool calls from model output for non-streaming mode.

        Args:
            model_output: Complete model output
            request: Chat completion request

        Returns:
            ExtractedToolCallInformation containing tool calls and content
        """
        processed_output = self.preprocess_model_output(model_output)

        if self.tool_call_start_token not in processed_output:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        try:
            function_call_tuples = self.tool_call_regex.findall(processed_output)

            raw_function_calls = []
            for match in function_call_tuples:
                tool_call_content = match[0] if match[0] else match[1]
                if tool_call_content.strip():
                    lines = tool_call_content.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if line and line.startswith("{") and line.endswith("}"):
                            try:
                                parsed_call = json.loads(line)
                                raw_function_calls.append(parsed_call)
                            except json.JSONDecodeError:
                                continue

            tool_calls = []
            for function_call in raw_function_calls:
                if "name" in function_call and "arguments" in function_call:
                    tool_calls.append(
                        ToolCall(
                            type="function",
                            function=FunctionCall(
                                name=function_call["name"],
                                arguments=json.dumps(
                                    function_call["arguments"], ensure_ascii=False
                                ),
                            ),
                        )
                    )

            processed_pos = processed_output.find(self.tool_call_start_token)
            if processed_pos != -1:
                processed_content = processed_output[:processed_pos].strip()

                if processed_content:
                    lines = processed_content.split("\n")
                    for line in reversed(lines):
                        line = line.strip()
                        if line:
                            pos = model_output.find(line)
                            if pos != -1:
                                content = model_output[: pos + len(line)]
                                break
                    else:
                        content = ""
                else:
                    content = ""
            else:
                content = model_output

            return ExtractedToolCallInformation(
                tools_called=len(tool_calls) > 0,
                tool_calls=tool_calls,
                content=content.strip() if content.strip() else None,
            )

        except Exception:
            logger.exception(
                "An unexpected error occurred during tool call extraction."
            )
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )