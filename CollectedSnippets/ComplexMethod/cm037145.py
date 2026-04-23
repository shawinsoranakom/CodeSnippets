def parse_delta(
        self,
        delta_text: str,
        delta_token_ids: list[int],
        request: ChatCompletionRequest | ResponsesRequest,
        prompt_token_ids: list[int] | None = None,
    ) -> DeltaMessage | None:
        state = self._stream_state

        if not state.prompt_reasoning_checked and prompt_token_ids is not None:
            state.prompt_reasoning_checked = True
            if self.is_reasoning_end(prompt_token_ids):
                state.reasoning_ended = True

        current_text = state.previous_text + delta_text
        current_token_ids = state.previous_token_ids + delta_token_ids
        delta_message: DeltaMessage | None = None

        # Reasoning extraction
        if self._in_reasoning_phase(state):
            delta_message = self.extract_reasoning_streaming(
                previous_text=state.previous_text,
                current_text=current_text,
                delta_text=delta_text,
                previous_token_ids=state.previous_token_ids,
                current_token_ids=current_token_ids,
                delta_token_ids=delta_token_ids,
            )
            # Hand off remaining content to tool parser
            if self._tool_parser and self.is_reasoning_end(delta_token_ids):
                state.reasoning_ended = True
                current_token_ids = self.extract_content_ids(delta_token_ids)
                if delta_message and delta_message.content:
                    current_text = delta_message.content
                    delta_message.content = None
                else:
                    current_text = ""

        # Tool call extraction
        if self._in_tool_call_phase(state):
            if not state.tool_call_text_started:
                state.tool_call_text_started = True
                state.previous_text = ""
                state.previous_token_ids = []
                delta_text = current_text
                delta_token_ids = current_token_ids
            delta_message = self.extract_tool_calls_streaming(
                previous_text=state.previous_text,
                current_text=current_text,
                delta_text=delta_text,
                previous_token_ids=state.previous_token_ids,
                current_token_ids=current_token_ids,
                delta_token_ids=delta_token_ids,
                request=request,  # type: ignore[arg-type]
            )

        # No parsers: pass through as content
        if self._reasoning_parser is None and self._tool_parser is None:
            delta_message = DeltaMessage(content=delta_text)

        state.previous_text = current_text
        state.previous_token_ids = current_token_ids
        return delta_message