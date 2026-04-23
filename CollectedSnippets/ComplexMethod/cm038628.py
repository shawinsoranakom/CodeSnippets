def _parse_tool_calls_from_content(
        request: ResponsesRequest | ChatCompletionRequest,
        tokenizer: TokenizerLike | None,
        enable_auto_tools: bool,
        tool_parser_cls: type[ToolParser] | None,
        content: str | None = None,
    ) -> tuple[list[FunctionCall] | None, str | None]:
        # When the Mistral grammar factory injected structured outputs,
        # let the parser handle the output.
        use_mistral_tool_parser = (
            isinstance(request, ChatCompletionRequest)
            and tool_parser_cls is not None
            and issubclass(tool_parser_cls, MistralToolParser)
            and request._grammar_from_tool_parser
        )

        function_calls = list[FunctionCall]()
        if (
            not use_mistral_tool_parser
            and request.tool_choice
            and isinstance(request.tool_choice, ToolChoiceFunction)
        ):
            assert content is not None
            # Forced Function Call (Responses API)
            function_calls.append(
                FunctionCall(name=request.tool_choice.name, arguments=content)
            )
            content = None  # Clear content since tool is called.
        elif (
            not use_mistral_tool_parser
            and request.tool_choice
            and isinstance(request.tool_choice, ChatCompletionNamedToolChoiceParam)
            and (tool_parser_cls is None or tool_parser_cls.supports_required_and_named)
        ):
            # Named function with standard JSON-based parsing
            assert content is not None
            function_calls.append(
                FunctionCall(name=request.tool_choice.function.name, arguments=content)
            )
            content = None  # Clear content since tool is called.
        elif (
            not use_mistral_tool_parser
            and request.tool_choice == "required"
            and (tool_parser_cls is None or tool_parser_cls.supports_required_and_named)
        ):
            # "required" with standard JSON-based parsing
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
            content = None  # Clear content since tool is called.
        elif tool_parser_cls and (
            use_mistral_tool_parser
            or (
                enable_auto_tools
                and (
                    request.tool_choice == "auto"
                    or request.tool_choice is None
                    or (
                        not tool_parser_cls.supports_required_and_named
                        and request.tools
                        and (
                            request.tool_choice == "required"
                            or isinstance(
                                request.tool_choice,
                                ChatCompletionNamedToolChoiceParam,
                            )
                        )
                    )
                )
            )
        ):
            # Automatic Tool Call Parsing (also used as fallback for
            # required/named when supports_required_and_named=False)
            if tokenizer is None:
                raise ValueError(
                    "Tokenizer not available when `skip_tokenizer_init=True`"
                )

            try:
                tool_parser = tool_parser_cls(tokenizer, request.tools)
            except RuntimeError as e:
                logger.exception("Error in tool parser creation.")
                raise e
            tool_call_info = tool_parser.extract_tool_calls(
                content if content is not None else "",
                request=request,  # type: ignore
            )
            if tool_call_info is not None and tool_call_info.tools_called:
                # extract_tool_calls() returns a list of tool calls.
                function_calls.extend(
                    FunctionCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                    for tool_call in tool_call_info.tool_calls
                )
                content = tool_call_info.content
                if content and content.strip() == "":
                    content = None
            else:
                # No tool calls.
                return None, content

        return function_calls, content