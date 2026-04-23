async def render_chat(
        self,
        request: ChatCompletionRequest,
    ) -> tuple[list[ConversationMessage], list[EngineInput]] | ErrorResponse:
        """Core preprocessing logic for chat requests (no model/engine check).

        Called directly by render_chat_request and delegated to by
        OpenAIServingChat.render_chat_request after its engine-aware checks.
        """
        tokenizer = self.renderer.tokenizer

        tool_parser = self.tool_parser

        if is_mistral_tokenizer(tokenizer):
            # because of issues with pydantic we need to potentially
            # re-serialize the tool_calls field of the request
            _mt.maybe_serialize_tool_calls(request)  # type: ignore[arg-type]
            _mt.truncate_tool_call_ids(request)  # type: ignore[arg-type]
            _mt.validate_request_params(request)

        # Check if tool parsing is unavailable (common condition)
        tool_parsing_unavailable = (
            tool_parser is None
            and not is_mistral_tokenizer(tokenizer)
            and not self.use_harmony
        )

        # Validate tool_choice when tool parsing is required but unavailable
        if tool_parsing_unavailable and request.tool_choice not in (
            None,
            "none",
        ):
            if request.tool_choice == "auto" and not self.enable_auto_tools:
                # for hf tokenizers, "auto" tools requires
                # --enable-auto-tool-choice and --tool-call-parser
                return self.create_error_response(
                    '"auto" tool choice requires '
                    "--enable-auto-tool-choice and --tool-call-parser to be set"
                )
            elif request.tool_choice != "auto":
                # "required" or named tool requires tool parser
                return self.create_error_response(
                    f'tool_choice="{request.tool_choice}" requires '
                    "--tool-call-parser to be set"
                )

        if request.tools is None or (
            request.tool_choice == "none" and self.exclude_tools_when_tool_choice_none
        ):
            tool_dicts = None
        else:
            tool_dicts = [tool.model_dump() for tool in request.tools]

        if not self.use_harmony:
            # Common case.
            error_check_ret = self.validate_chat_template(
                request_chat_template=request.chat_template,
                chat_template_kwargs=request.chat_template_kwargs,
                trust_request_chat_template=self.trust_request_chat_template,
            )
            if error_check_ret is not None:
                return error_check_ret

            conversation, engine_inputs = await self.preprocess_chat(
                request,
                request.messages,
                default_template=self.chat_template,
                default_template_content_format=self.chat_template_content_format,
                default_template_kwargs=self.default_chat_template_kwargs,
                tool_dicts=tool_dicts,
                tool_parser=tool_parser,
                skip_mm_cache=True,
                reasoning_parser=self.reasoning_parser,
            )
        else:
            # For GPT-OSS.
            should_include_tools = tool_dicts is not None
            conversation, engine_inputs = self._make_request_with_harmony(
                request, should_include_tools
            )

        return conversation, engine_inputs