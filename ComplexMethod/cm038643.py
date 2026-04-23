async def _process_harmony_streaming_events(
        self,
        request: ResponsesRequest,
        sampling_params: SamplingParams,
        result_generator: AsyncIterator[ConversationContext | None],
        context: ConversationContext,
        model_name: str,
        tokenizer: TokenizerLike,
        request_metadata: RequestResponseMetadata,
        created_time: int,
        _increment_sequence_number_and_return: Callable[
            [StreamingResponsesResponse], StreamingResponsesResponse
        ],
    ) -> AsyncGenerator[StreamingResponsesResponse, None]:
        state = StreamingState()

        async for ctx in result_generator:
            assert isinstance(ctx, StreamingHarmonyContext)

            # finish_reason='error' indicates a retryable error
            self._raise_if_error(ctx.finish_reason, request.request_id)

            if ctx.is_expecting_start():
                if len(ctx.parser.messages) > 0:
                    previous_item = ctx.parser.messages[-1]
                    for event in emit_previous_item_done_events(previous_item, state):
                        yield _increment_sequence_number_and_return(event)
                state.reset_for_new_item()

            # Stream the output of a harmony message
            for event in emit_content_delta_events(ctx, state):
                yield _increment_sequence_number_and_return(event)

            # Stream tool call outputs
            for event in emit_tool_action_events(ctx, state, self.tool_server):
                yield _increment_sequence_number_and_return(event)