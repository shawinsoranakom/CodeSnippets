async def create_completion(
        self,
        request: CompletionRequest,
        raw_request: Request | None = None,
    ) -> AsyncGenerator[str, None] | CompletionResponse | ErrorResponse:
        """Completion API similar to OpenAI's API.

        See https://platform.openai.com/docs/api-reference/completions/create
        for the API specification. This API mimics the OpenAI Completion API.

        NOTE: Currently we do not support the following feature:
            - suffix (the language models we currently support do not support
            suffix)
        """
        if request.stream and request.use_beam_search:
            return self.create_error_response(
                "Streaming is not currently supported with beam search"
            )

        result = await self.render_completion_request(request)
        if isinstance(result, ErrorResponse):
            return result

        engine_inputs = result

        request_id = f"cmpl-{self._base_request_id(raw_request, request.request_id)}"
        created_time = int(time.time())

        request_metadata = RequestResponseMetadata(request_id=request_id)
        if raw_request:
            raw_request.state.request_metadata = request_metadata

        lora_request = self._maybe_get_adapters(request)

        # Extract data_parallel_rank from header (router can inject it)
        data_parallel_rank = self._get_data_parallel_rank(raw_request)

        # Schedule the request and get the result generator.
        max_model_len = self.model_config.max_model_len
        generators: list[AsyncGenerator[RequestOutput, None]] = []
        for i, engine_input in enumerate(engine_inputs):
            max_tokens = get_max_tokens(
                max_model_len,
                request.max_tokens,
                self._extract_prompt_len(engine_input),
                self.default_sampling_params,
                self.override_max_tokens,
            )

            sampling_params: SamplingParams | BeamSearchParams
            if request.use_beam_search:
                sampling_params = request.to_beam_search_params(
                    max_tokens, self.default_sampling_params
                )
            else:
                sampling_params = request.to_sampling_params(
                    max_tokens,
                    self.default_sampling_params,
                )

            request_id_item = f"{request_id}-{i}"

            self._log_inputs(
                request_id_item,
                engine_input,
                params=sampling_params,
                lora_request=lora_request,
            )

            trace_headers = (
                None
                if raw_request is None
                else await self._get_trace_headers(raw_request.headers)
            )

            if isinstance(sampling_params, BeamSearchParams):
                generator = self.beam_search(
                    prompt=engine_input,
                    request_id=request_id,
                    params=sampling_params,
                    lora_request=lora_request,
                    trace_headers=trace_headers,
                )
            else:
                generator = self.engine_client.generate(
                    engine_input,
                    sampling_params,
                    request_id_item,
                    lora_request=lora_request,
                    trace_headers=trace_headers,
                    priority=request.priority,
                    data_parallel_rank=data_parallel_rank,
                )

            generators.append(generator)

        result_generator = merge_async_iterators(*generators)

        model_name = self.models.model_name(lora_request)
        num_prompts = len(engine_inputs)

        # Streaming response
        tokenizer = self.renderer.tokenizer

        if request.stream:
            return self.completion_stream_generator(
                request,
                engine_inputs,
                result_generator,
                request_id,
                created_time,
                model_name,
                num_prompts=num_prompts,
                tokenizer=tokenizer,
                request_metadata=request_metadata,
            )

        # Non-streaming response
        final_res_batch: list[RequestOutput | None] = [None] * num_prompts
        try:
            async for i, res in result_generator:
                final_res_batch[i] = res

            for i, final_res in enumerate(final_res_batch):
                assert final_res is not None

                # The output should contain the input text
                # We did not pass it into vLLM engine to avoid being redundant
                # with the inputs token IDs
                if final_res.prompt is None:
                    final_res.prompt = self._extract_prompt_text(engine_inputs[i])

            final_res_batch_checked = cast(list[RequestOutput], final_res_batch)

            response = self.request_output_to_completion_response(
                final_res_batch_checked,
                request,
                request_id,
                created_time,
                model_name,
                tokenizer,
                request_metadata,
            )
        except asyncio.CancelledError:
            return self.create_error_response("Client disconnected")

        # When user requests streaming but we don't stream, we still need to
        # return a streaming response with a single event.
        if request.stream:
            response_json = response.model_dump_json()

            async def fake_stream_generator() -> AsyncGenerator[str, None]:
                yield f"data: {response_json}\n\n"
                yield "data: [DONE]\n\n"

            return fake_stream_generator()

        return response