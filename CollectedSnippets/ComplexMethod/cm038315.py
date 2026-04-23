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
        until a complete ``<invoke>...</invoke>`` block is available, then
        parsed and emitted in one shot.
        """

        start_in_text = self.tool_call_start_token in delta_text
        start_in_ids = self.tool_call_start_token_id in delta_token_ids
        tool_call_starting = start_in_text or start_in_ids
        # Reset state on new request (parser is reused) or new tool-call block.
        if not previous_text or tool_call_starting:
            self.current_tool_index = 0
            self.prev_tool_call_arr.clear()
            self.streamed_args_for_tool.clear()
            self.is_tool_call_started = tool_call_starting

        # Pass through content before any tool call.
        if not self.is_tool_call_started:
            return DeltaMessage(content=delta_text) if delta_text else None

        # Capture content before the start token.
        content_before = None
        if start_in_text:
            before = delta_text[: delta_text.index(self.tool_call_start_token)]
            content_before = before or None

        # Extract newly completed <invoke> blocks as DeltaToolCalls.
        delta_tool_calls = self._extract_delta_tool_calls(current_text, request)

        if delta_tool_calls or content_before:
            return DeltaMessage(
                content=content_before,
                tool_calls=delta_tool_calls,
            )

        # EOS and </minimax:tool_call> both arrive as special tokens with
        # no decoded text. Return non-None for EOS so the serving framework
        # reaches the finish-reason handling path instead of skipping.
        if (
            not delta_text
            and delta_token_ids
            and self.prev_tool_call_arr
            and self.tool_call_end_token_id not in delta_token_ids
        ):
            return DeltaMessage(content="")

        return None