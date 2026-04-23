def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],  # pylint: disable=unused-argument
        current_token_ids: Sequence[int],  # pylint: disable=unused-argument
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        """Extract tool calls from streaming model output.

        Uses a buffer-until-complete-invoke strategy: tokens are buffered
        until a complete invoke block is available, then parsed and emitted
        in one shot.
        """

        # First chunk of a new stream — reset state from prior request.
        if not previous_text:
            self._reset_streaming_state()

        # Detect whether we've entered the tool-call region.
        # Use current_text (not delta_text) since the start token may
        # be split across chunks.
        content_before = None
        if self.is_tool_call_started:
            pass
        elif self.tool_call_start_token in current_text:
            # Tool-call region found, capture any plain text before it.
            self.is_tool_call_started = True
            start_idx = current_text.index(self.tool_call_start_token)
            content_before = current_text[len(previous_text) : start_idx] or None
        else:
            # Still in plain-text region, forward as content.
            return DeltaMessage(content=delta_text) if delta_text else None

        # Inside tool-call region: emit any newly completed invokes.
        delta_tool_calls = self._extract_delta_tool_calls(current_text, request)

        if delta_tool_calls or content_before:
            return DeltaMessage(
                content=content_before,
                tool_calls=delta_tool_calls,
            )

        # Empty delta with token ids means EOS or closing tag; return
        # non-None so the serving framework can finalize finish_reason.
        if not delta_text and delta_token_ids and self.prev_tool_call_arr:
            return DeltaMessage(content="")

        return None