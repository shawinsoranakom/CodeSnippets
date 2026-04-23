def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        if self.TOOL_CALLS_BEGIN not in model_output:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        pre_text, rest = model_output.split(self.TOOL_CALLS_BEGIN, 1)
        if self.TOOL_CALLS_END not in rest:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        tool_block, post_text = rest.split(self.TOOL_CALLS_END, 1)
        content = (pre_text + post_text).strip()

        tool_calls: list[ToolCall] = []
        call_parts = tool_block.split(self.TOOL_CALL_BEGIN)

        for part in call_parts:
            if not part or self.TOOL_CALL_END not in part:
                continue

            call_content = part.split(self.TOOL_CALL_END, 1)[0]
            if self.TOOL_SEP not in call_content:
                continue

            type_part, invoke_part = call_content.split(self.TOOL_SEP, 1)
            if type_part.strip() != "function":
                continue

            function_name, params_dict = self._parse_steptml_invoke(invoke_part)

            if function_name and params_dict is not None:
                params_dict = self._cast_arguments(function_name, params_dict)
                params_str = json.dumps(params_dict, ensure_ascii=False)
                tool_calls.append(
                    ToolCall(
                        function=FunctionCall(name=function_name, arguments=params_str)
                    )
                )
        if tool_calls:
            return ExtractedToolCallInformation(
                tools_called=True,
                tool_calls=tool_calls,
                content=content if content else None,
            )
        return ExtractedToolCallInformation(
            tools_called=False, tool_calls=[], content=model_output
        )