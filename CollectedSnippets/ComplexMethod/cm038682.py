async def preprocess_chat(
        self,
        request: Any,
        messages: list[Any],
        default_template: str | None,
        default_template_content_format: ChatTemplateContentFormatOption,
        default_template_kwargs: dict[str, Any] | None,
        tool_dicts: list[dict[str, Any]] | None = None,
        tool_parser: type[ToolParser] | None = None,
        reasoning_parser: type[ReasoningParser] | None = None,
        *,
        skip_mm_cache: bool = False,
    ) -> tuple[list[ConversationMessage], list[EngineInput]]:
        """Copied from OpenAIServing._preprocess_chat."""
        renderer = self.renderer
        mm_config = self.model_config.multimodal_config

        default_template_kwargs = merge_kwargs(
            default_template_kwargs,
            dict(
                tools=tool_dicts,
                tokenize=is_mistral_tokenizer(renderer.tokenizer),
            ),
        )

        tok_params = request.build_tok_params(self.model_config)
        chat_params = request.build_chat_params(
            default_template, default_template_content_format
        ).with_defaults(
            default_template_kwargs,
            default_media_io_kwargs=(mm_config.media_io_kwargs if mm_config else None),
            default_mm_processor_kwargs=getattr(request, "mm_processor_kwargs", None),
        )

        (conversation,), (engine_input,) = await renderer.render_chat_async(
            [messages],
            chat_params,
            tok_params,
            prompt_extras={
                k: v
                for k in ("mm_processor_kwargs", "cache_salt")
                if (v := getattr(request, k, None)) is not None
            },
            skip_mm_cache=skip_mm_cache,
        )

        if reasoning_parser is not None:
            tokenizer = renderer.get_tokenizer()
            request = reasoning_parser(
                tokenizer,
                model_config=self.model_config,
                chat_template_kwargs=chat_params.chat_template_kwargs,
            ).adjust_request(request=request)

        # tool parsing is done only if a tool_parser has been set and if
        # tool_choice is not "none" (if tool_choice is "none" but a tool_parser
        # is set, we want to prevent parsing a tool_call hallucinated by the LLM
        #
        # Exception: Mistral grammar-capable tokenizers always call
        # adjust_request — even for tool_choice="none" — so that the grammar
        # factory can prevent special-token leakage.
        if tool_parser is not None:
            tool_choice = getattr(request, "tool_choice", "none")
            tokenizer = renderer.get_tokenizer()
            is_mistral_grammar_eligible = (
                issubclass(tool_parser, MistralToolParser)
                and is_mistral_tokenizer(tokenizer)
                and tokenizer.supports_grammar
            )
            if tool_choice != "none" or is_mistral_grammar_eligible:
                if not isinstance(request, ChatCompletionRequest | ResponsesRequest):
                    msg = (
                        "Tool usage is only supported "
                        "for Chat Completions API or Responses API requests, "
                        f"but got {type(request).__name__}"
                    )
                    raise NotImplementedError(msg)
                request = tool_parser(tokenizer, request.tools).adjust_request(
                    request=request
                )

        return conversation, [engine_input]