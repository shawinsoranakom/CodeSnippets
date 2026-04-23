def extract_maybe_reasoning_and_tool_streaming(
        self,
        *,
        reasoning_parser: ReasoningParser | None,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: list[int],
        current_token_ids: list[int],
        output_token_ids: Sequence[int],
        reasoning_ended: bool,
        prompt_is_reasoning_end: bool | None,
        request: ChatCompletionRequest,
    ) -> MistralStreamingResult:
        r"""Streaming extraction with reasoning followed by tool-call parsing.

        This method encapsulates the combined reasoning extraction and
        tool-call streaming logic so that the serving layer only needs a
        thin routing branch.

        The flow is:

        1. If a *reasoning_parser* is present and reasoning has **not** ended,
           extract reasoning tokens.  Pre-v15 models may have pre-filled
           `[THINK]...[/THINK]` in system prompts, so we skip the
           prompt-level reasoning-end check for those.
        2. Once reasoning ends (or if there is no reasoning parser), delegate
           to `extract_tool_calls_streaming` and track whether tools were
           called.

        Args:
            reasoning_parser: Optional reasoning parser instance.
            previous_text: Accumulated text from prior chunks.
            current_text: Full accumulated text including current chunk.
            delta_text: New text in this chunk.
            previous_token_ids: Token ids from prior chunks.
            current_token_ids: Full token ids including current chunk.
            output_token_ids: Raw output token ids from the engine.
            reasoning_ended: Whether reasoning has already ended.
            prompt_is_reasoning_end: Whether the prompt itself ends reasoning.
            request: The originating chat completion request.
        """
        delta_message: DeltaMessage | None = None
        tools_called = False
        reasoning_ended_at_entry = reasoning_ended

        # For MistralReasoningParser, only enter the reasoning block when
        # the model has actually emitted a [THINK] token.  Other reasoning
        # parsers always expect thinking to be present.
        expect_thinking = (
            not isinstance(reasoning_parser, MistralReasoningParser)
            or reasoning_parser.start_token_id in current_token_ids
        )
        if reasoning_parser is not None and not reasoning_ended and expect_thinking:
            # Pre-v15 models may have pre-filled [THINK]...[/THINK] in
            # system prompts, so skip the prompt-level reasoning-end
            # check and wait for the output's own end-of-think.
            is_pre_v15 = (
                isinstance(self.model_tokenizer, MistralTokenizer)
                and self.model_tokenizer.version < 15
            )

            if not is_pre_v15 and prompt_is_reasoning_end:
                reasoning_ended = True
                current_token_ids = list(output_token_ids)
            else:
                delta_message = reasoning_parser.extract_reasoning_streaming(
                    previous_text,
                    current_text,
                    delta_text,
                    previous_token_ids,
                    current_token_ids,
                    output_token_ids,
                )
                if reasoning_parser.is_reasoning_end_streaming(
                    current_token_ids, output_token_ids
                ):
                    reasoning_ended = True
                    current_token_ids = reasoning_parser.extract_content_ids(
                        list(output_token_ids)
                    )
                    if delta_message and delta_message.content:
                        current_text = delta_message.content
                        delta_message.content = None
                    else:
                        current_text = ""

            if not reasoning_ended:
                return MistralStreamingResult(
                    delta_message=delta_message,
                    reasoning_ended=False,
                    tools_called=False,
                    current_text=current_text,
                    current_token_ids=current_token_ids,
                )

        delta_token_ids = list(output_token_ids)

        # On the iteration where reasoning just ended, reset the text/token
        # state so the tool parser sees a clean history instead of the
        # accumulated reasoning text.
        if not reasoning_ended_at_entry and reasoning_ended:
            previous_text = ""
            previous_token_ids = []
            delta_text = current_text
            delta_token_ids = current_token_ids

        delta_message = self.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=previous_token_ids,
            current_token_ids=current_token_ids,
            delta_token_ids=delta_token_ids,
            request=request,
        )
        if delta_message and delta_message.tool_calls:
            tools_called = True

        return MistralStreamingResult(
            delta_message=delta_message,
            reasoning_ended=reasoning_ended,
            tools_called=tools_called,
            current_text=current_text,
            current_token_ids=current_token_ids,
        )