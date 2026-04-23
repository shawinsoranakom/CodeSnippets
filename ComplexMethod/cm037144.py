def _parse_tool_calls(
        self,
        request: ResponsesRequest,
        content: str | None,
        enable_auto_tools: bool,
    ) -> tuple[list[FunctionCall], str | None]:
        """
        TODO(qandrew): merge _parse_tool_calls_from_content
        for ChatCompletions into this function
        Parse tool calls from content based on request tool_choice settings.

        Returns:
            A tuple of (function_calls, remaining_content) if tool calls
            were parsed
        """
        function_calls: list[FunctionCall] = []

        if request.tool_choice and isinstance(request.tool_choice, ToolChoiceFunction):
            # Forced Function Call (Responses API style)
            assert content is not None
            function_calls.append(
                FunctionCall(name=request.tool_choice.name, arguments=content)
            )
            return function_calls, None  # Clear content since tool is called.

        if request.tool_choice and isinstance(
            request.tool_choice, ChatCompletionNamedToolChoiceParam
        ):
            # Forced Function Call (Chat Completion API style)
            assert content is not None
            function_calls.append(
                FunctionCall(name=request.tool_choice.function.name, arguments=content)
            )
            return function_calls, None  # Clear content since tool is called.

        if request.tool_choice == "required":
            # Required tool calls - parse JSON
            tool_calls = []
            with contextlib.suppress(ValidationError):
                content = content or ""
                tool_calls = TypeAdapter(list[FunctionDefinition]).validate_json(
                    content
                )
            for tool_call in tool_calls:
                function_calls.append(
                    FunctionCall(
                        name=tool_call.name,
                        arguments=json.dumps(tool_call.parameters, ensure_ascii=False),
                    )
                )
            return function_calls, None  # Clear content since tool is called.

        if (
            self._tool_parser is not None
            and enable_auto_tools
            and (request.tool_choice == "auto" or request.tool_choice is None)
        ):
            # Automatic Tool Call Parsing
            tool_call_info = self._tool_parser.extract_tool_calls(
                content if content is not None else "",
                request=request,  # type: ignore
            )
            if tool_call_info is not None and tool_call_info.tools_called:
                function_calls.extend(
                    FunctionCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                    for tool_call in tool_call_info.tool_calls
                )
                remaining_content = tool_call_info.content
                if remaining_content and remaining_content.strip() == "":
                    remaining_content = None
                return function_calls, remaining_content

        # No tool calls
        return [], content