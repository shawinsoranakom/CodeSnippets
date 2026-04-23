def adjust_request(
        self, request: ChatCompletionRequest | ResponsesRequest
    ) -> ChatCompletionRequest | ResponsesRequest:
        so_non_supported_attributes = [
            "regex",
            "choice",
            "grammar",
            # whitespace_pattern is not a constraint type but an option;
            # Mistral grammar factory does not support it.
            "whitespace_pattern",
            "structural_tag",
        ]
        any_so_non_supported_active = request.structured_outputs is not None and any(
            getattr(request.structured_outputs, attribute) is not None
            for attribute in so_non_supported_attributes
        )
        response_format_non_supported_active = (
            isinstance(request, ResponsesRequest)
            or request.response_format is not None
            and request.response_format.type == "structural_tag"
        )

        if (
            not is_mistral_tokenizer(self.model_tokenizer)
            or isinstance(request, ResponsesRequest)
            or not self.model_tokenizer.supports_grammar
            or any_so_non_supported_active
            or response_format_non_supported_active
        ):
            request = super().adjust_request(request)
            if request.tools and request.tool_choice != "none":
                # Do not skip special tokens when using chat template
                # with Mistral parser as TOOL_CALL token is needed
                # for tool detection.
                # Note: we don't want skip_special_tokens=False
                # with MistralTokenizer as it is incompatible
                request.skip_special_tokens = False
            return request

        json_schema: dict[str, Any] | None = None
        if request.structured_outputs is not None:
            if request.structured_outputs.json_object is not None:
                json_schema = _DEFAULT_JSON_SCHEMA
            elif request.structured_outputs.json is not None:
                if isinstance(request.structured_outputs.json, str):
                    json_schema = json.loads(request.structured_outputs.json)
                else:
                    json_schema = request.structured_outputs.json
            else:
                raise ValueError(
                    "Unsupported request.structured_outputs for MistralToolParser. "
                    "Only `json` and `json_object` are supported."
                )
        elif (
            request.response_format is not None
            and request.response_format.type != "text"
        ):
            if request.response_format.type == "json_object":
                json_schema = _DEFAULT_JSON_SCHEMA
            elif request.response_format.type == "json_schema":
                if request.response_format.json_schema is not None:
                    json_schema = request.response_format.json_schema.json_schema
                else:
                    json_schema = _DEFAULT_JSON_SCHEMA
            else:
                raise ValueError(
                    "MistralToolParser only accepts `text`, `json_object` or "
                    f"`json_schema`, got {request.response_format=}"
                )
            # Structured Outputs will be defined.
            request.response_format = None

        grammar_factory = self.model_tokenizer.grammar_factory

        # TODO: Once unified parser, improve this.
        # The issue is figuring out when a model is a reasoning one or not.
        template = grammar_factory.select_jinja_template(
            reasoning=self.model_can_reason
        )

        mistral_tools = (
            [
                MistralTool.model_validate(
                    adapt_inplace_to_mistral_tool(tool.model_dump())
                )
                for tool in request.tools
            ]
            if request.tools is not None
            else None
        )

        tool_choice: MistralToolChoice
        match request.tool_choice:
            case "none" | "auto" | "required":
                tool_choice = MistralToolChoiceEnum(request.tool_choice)
            case None:
                tool_choice = MistralToolChoiceEnum.auto
            # _ == Named tool choice
            case _:
                tool_choice = MistralNamedToolChoice.model_validate(
                    {
                        "type": "function",
                        "function": {"name": request.tool_choice.function.name},
                    }
                )

        # Rendering grammar is cached in mistral-common given tools, template and mode.
        match tool_choice, json_schema is not None:
            case MistralToolChoiceEnum.none, True:
                lark_grammar = grammar_factory.get_lark_for_json_schema(
                    template=template, json_schema=json_schema
                )
            case _, _:
                lark_grammar = grammar_factory.get_lark_from_jinja(
                    template=template,
                    mode=tool_choice,
                    tools=mistral_tools,
                    json_schema=json_schema,
                    parallel_tool_calls=request.parallel_tool_calls,
                    json_only=False,
                )

        request.structured_outputs = StructuredOutputsParams(grammar=lark_grammar)
        request._grammar_from_tool_parser = True
        return request