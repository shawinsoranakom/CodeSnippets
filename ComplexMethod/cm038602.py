async def create_batch_chat_completion(
        self,
        request: BatchChatCompletionRequest,
        raw_request: Request | None = None,
    ) -> ChatCompletionResponse | ErrorResponse:
        """Batch Chat Completion endpoint (/v1/chat/completions/batch).

        Processes N conversations from a single request concurrently and
        returns one choice per conversation indexed 0, 1, ..., N-1.
        Streaming, tool use, and beam search are not supported.
        """
        tokenizer = self.renderer.tokenizer
        assert tokenizer is not None
        single_requests = [
            request.to_chat_completion_request(messages)
            for messages in request.messages
        ]

        reasoning_parser: ReasoningParser | None = None
        if self.reasoning_parser_cls:
            chat_template_kwargs = self._effective_chat_template_kwargs(
                single_requests[0]
            )
            reasoning_parser = self.reasoning_parser_cls(
                tokenizer,
                chat_template_kwargs=chat_template_kwargs,  # type: ignore[call-arg]
            )

        render_result = await self.render_batch_chat_request(request)
        if isinstance(render_result, ErrorResponse):
            return render_result
        all_conversations, engine_prompts = render_result

        request_id = (
            f"chatcmpl-{self._base_request_id(raw_request, request.request_id)}"
        )
        request_metadata = RequestResponseMetadata(request_id=request_id)
        if raw_request:
            raw_request.state.request_metadata = request_metadata

        lora_request = self._maybe_get_adapters(request, supports_default_mm_loras=True)
        model_name = self.models.model_name(lora_request)
        data_parallel_rank = self._get_data_parallel_rank(raw_request)
        max_model_len = self.model_config.max_model_len

        generators: list[AsyncGenerator[RequestOutput, None]] = []
        for i, engine_prompt in enumerate(engine_prompts):
            sub_request_id = f"{request_id}_{i}"
            max_tokens = get_max_tokens(
                max_model_len,
                request.max_completion_tokens
                if request.max_completion_tokens is not None
                else request.max_tokens,
                self._extract_prompt_len(engine_prompt),
                self.default_sampling_params,
                self.override_max_tokens,
            )
            single_request = single_requests[i]
            sampling_params = single_request.to_sampling_params(
                max_tokens, self.default_sampling_params
            )
            self._log_inputs(
                sub_request_id,
                engine_prompt,
                params=sampling_params,
                lora_request=lora_request,
            )
            trace_headers = (
                None
                if raw_request is None
                else await self._get_trace_headers(raw_request.headers)
            )
            generators.append(
                self.engine_client.generate(
                    engine_prompt,
                    sampling_params,
                    sub_request_id,
                    lora_request=lora_request,
                    trace_headers=trace_headers,
                    priority=request.priority if hasattr(request, "priority") else 0,
                    data_parallel_rank=data_parallel_rank,
                    reasoning_ended=None,
                )
            )

        return await self.chat_completion_full_generator_batch(
            request,  # type: ignore[arg-type]
            generators,
            request_id,
            model_name,
            all_conversations,
            tokenizer,
            request_metadata,
            reasoning_parser,
        )