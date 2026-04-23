async def responses_full_generator(
        self,
        request: ResponsesRequest,
        sampling_params: SamplingParams,
        result_generator: AsyncIterator[ConversationContext],
        context: ConversationContext,
        model_name: str,
        tokenizer: TokenizerLike,
        request_metadata: RequestResponseMetadata,
        created_time: int | None = None,
    ) -> ErrorResponse | ResponsesResponse:
        if created_time is None:
            created_time = int(time.time())

        async with AsyncExitStack() as exit_stack:
            try:
                await self._initialize_tool_sessions(request, context, exit_stack)
                async for _ in result_generator:
                    pass
            except asyncio.CancelledError:
                return self.create_error_response("Client disconnected")

        # NOTE: Implementation of status is still WIP, but for now
        # we guarantee that if the status is not "completed", it is accurate.
        # "completed" is implemented as the "catch-all" for now.
        status: ResponseStatus = "completed"

        input_messages: ResponseInputOutputMessage | None = None
        output_messages: ResponseInputOutputMessage | None = None
        if self.use_harmony:
            assert isinstance(context, HarmonyContext)
            output = self._make_response_output_items_with_harmony(context)
            if request.enable_response_messages:
                input_messages = context.messages[: context.num_init_messages]
                output_messages = context.messages[context.num_init_messages :]
            num_tool_output_tokens = context.num_tool_output_tokens
            if len(output) > 0:
                if context.finish_reason == "length":
                    status = "incomplete"
                elif context.finish_reason == "abort":
                    status = "cancelled"
                else:
                    self._raise_if_error(context.finish_reason, request.request_id)
            else:
                status = "incomplete"
        elif isinstance(context, ParsableContext):
            output = context.parser.make_response_output_items_from_parsable_context()

            if request.enable_response_messages:
                input_messages = context.input_messages
                output_messages = context.output_messages

            # TODO: Calculate usage.
            # assert final_res.prompt_token_ids is not None
            num_tool_output_tokens = 0

            # Check finish reason from the parser
            if context.parser.finish_reason == "length":
                status = "incomplete"
        else:
            assert isinstance(context, SimpleContext)
            # Use final_output which has accumulated text/token_ids/logprobs
            final_res = context.final_output
            assert final_res is not None
            assert len(final_res.outputs) == 1
            final_output = final_res.outputs[0]

            # finish_reason='error' indicates retryable internal error
            self._raise_if_error(final_output.finish_reason, request.request_id)

            # Check if generation was stopped due to max_tokens
            if final_output.finish_reason == "length":
                status = "incomplete"

            output = self._make_response_output_items(request, final_output, tokenizer)

            if request.enable_response_messages:
                input_messages = context.input_messages
                output_messages = context.output_messages

            # Calculate usage.
            assert final_res.prompt_token_ids is not None
            num_tool_output_tokens = 0

        assert isinstance(context, (SimpleContext, HarmonyContext, ParsableContext))
        num_prompt_tokens = context.num_prompt_tokens
        num_generated_tokens = context.num_output_tokens
        num_cached_tokens = context.num_cached_tokens
        num_reasoning_tokens = context.num_reasoning_tokens
        # For text-based reasoning parsers (e.g., <think>...</think>),
        # HarmonyContext already counts reasoning tokens via channels.
        # For Simple/Parsable contexts, derive reasoning_tokens from
        # accumulated output token IDs using the parser if not already set.
        if (
            num_reasoning_tokens == 0
            and self.parser is not None
            and self.parser.reasoning_parser_cls is not None
            and isinstance(context, (SimpleContext, ParsableContext))
        ):
            reasoning_parser = self.parser.reasoning_parser_cls(
                tokenizer,
                chat_template_kwargs=self._effective_chat_template_kwargs(request),
            )
            accumulated = getattr(context, "_accumulated_token_ids", []) or []
            num_reasoning_tokens = reasoning_parser.count_reasoning_tokens(accumulated)

        usage = ResponseUsage(
            input_tokens=num_prompt_tokens,
            output_tokens=num_generated_tokens,
            total_tokens=num_prompt_tokens + num_generated_tokens,
            input_tokens_details=InputTokensDetails(
                cached_tokens=num_cached_tokens,
                input_tokens_per_turn=[
                    turn.input_tokens for turn in context.all_turn_metrics
                ],
                cached_tokens_per_turn=[
                    turn.cached_input_tokens for turn in context.all_turn_metrics
                ],
            ),
            output_tokens_details=OutputTokensDetails(
                reasoning_tokens=num_reasoning_tokens,
                tool_output_tokens=num_tool_output_tokens,
                output_tokens_per_turn=[
                    turn.output_tokens for turn in context.all_turn_metrics
                ],
                tool_output_tokens_per_turn=[
                    turn.tool_output_tokens for turn in context.all_turn_metrics
                ],
            ),
        )
        response = ResponsesResponse.from_request(
            request,
            sampling_params,
            input_messages=input_messages,
            output_messages=output_messages,
            model_name=model_name,
            created_time=created_time,
            output=output,
            status=status,
            usage=usage,
            kv_transfer_params=context.kv_transfer_params,
        )

        if request.store:
            async with self.response_store_lock:
                stored_response = self.response_store.get(response.id)
                # If the response is already cancelled, don't update it.
                if stored_response is None or stored_response.status != "cancelled":
                    self.response_store[response.id] = response
        return response