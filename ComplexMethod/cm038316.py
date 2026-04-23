def extract_tool_calls(
        self,
        model_output: str,
        request: ChatCompletionRequest,
    ) -> ExtractedToolCallInformation:
        function_call = None
        content = None
        if model_output.rstrip().endswith("</s>"):
            model_output = model_output[: model_output.rfind("</s>")]
        m_func = REGEX_FUNCTION_CALL.search(model_output)
        if m_func:
            try:
                function_call = json.loads(m_func.group(1), strict=False)
                if (
                    isinstance(function_call, dict)
                    and "name" in function_call
                    and "arguments" in function_call
                ):
                    if not isinstance(function_call["arguments"], dict):
                        function_call = None
                else:
                    function_call = None
            except json.JSONDecodeError:
                return ExtractedToolCallInformation(
                    tools_called=False,
                    tool_calls=[],
                    content=model_output,
                )
        m_content = REGEX_CONTENT_PATTERN.search(model_output)
        content = m_content.group(1) if m_content else model_output
        if not function_call:
            return ExtractedToolCallInformation(
                tools_called=False,
                tool_calls=[],
                content=content if content else None,
            )
        name = function_call["name"]
        args = function_call["arguments"]
        if not isinstance(args, str):
            args = json.dumps(function_call["arguments"], ensure_ascii=False)
        return ExtractedToolCallInformation(
            tools_called=True,
            tool_calls=[
                ToolCall(
                    type="function",
                    function=FunctionCall(
                        name=name,
                        arguments=args,
                    ),
                )
            ],
            content=content if content else None,
        )