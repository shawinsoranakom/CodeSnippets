def _handle_stream_event(
        self, evt: StreamEvent, responses: list[StreamBaseResponse]
    ) -> None:
        """Translate raw Anthropic streaming events into wire events.

        Handles four event types; everything else (``message_delta``
        stop reasons, ``signature_delta``, ``input_json_delta``,
        ``ping``, ...) is ignored because the summary ``AssistantMessage``
        carries their effects.

        * ``message_start`` — new message boundary, reset per-index maps
        * ``content_block_start`` — open text / reasoning block on the
          wire and remember the block type at that index
        * ``content_block_delta`` — forward ``text_delta`` immediately
          and coalesce ``thinking_delta`` (64-char / 50 ms window)
        * ``content_block_stop`` — drain any buffered thinking and close
          the corresponding wire block
        """
        raw: dict[str, Any] = evt.event or {}
        event_type = raw.get("type")

        if event_type == "message_start":
            self._reset_partial_stream_state()
            return

        if event_type == "content_block_start":
            block = raw.get("content_block") or {}
            index = raw.get("index")
            block_type = block.get("type")
            if not isinstance(index, int) or not isinstance(block_type, str):
                return
            self._block_types_by_index[index] = block_type
            if block_type == "text":
                self._end_reasoning_if_open(responses)
                self._ensure_text_started(responses)
                # Seed any preamble the block_start carries.
                seed = block.get("text") or ""
                if seed:
                    responses.append(StreamTextDelta(id=self.text_block_id, delta=seed))
                    self._partial_text_buffer += seed
                    self._text_since_last_tool_result = True
            elif block_type == "thinking":
                self._end_text_if_open(responses)
                self._ensure_reasoning_started(responses)
                self._last_thinking_flush_monotonic = time.monotonic()
            # tool_use / server_tool_use / redacted_thinking blocks stay
            # on the ``AssistantMessage`` path — the frontend widgets
            # need the final ``input`` payload which only arrives in the
            # summary.
            return

        if event_type == "content_block_delta":
            index = raw.get("index")
            if not isinstance(index, int):
                return
            delta = raw.get("delta") or {}
            delta_type = delta.get("type")
            if delta_type == "text_delta":
                chunk = delta.get("text") or ""
                if not chunk:
                    return
                self._ensure_text_started(responses)
                responses.append(StreamTextDelta(id=self.text_block_id, delta=chunk))
                self._partial_text_buffer += chunk
                self._text_since_last_tool_result = True
            elif delta_type == "thinking_delta":
                chunk = delta.get("thinking") or ""
                if not chunk:
                    return
                self._ensure_reasoning_started(responses)
                # Flush the coalesce buffer if the index changed — shouldn't
                # happen in practice but guard against interleaved indices.
                if (
                    self._pending_thinking_index is not None
                    and self._pending_thinking_index != index
                ):
                    self._flush_pending_thinking(responses)
                self._pending_thinking_delta += chunk
                self._pending_thinking_index = index
                now = time.monotonic()
                elapsed_ms = (now - self._last_thinking_flush_monotonic) * 1000.0
                if (
                    len(self._pending_thinking_delta) >= _THINKING_COALESCE_MIN_CHARS
                    or elapsed_ms >= _THINKING_COALESCE_MAX_INTERVAL_MS
                ):
                    self._flush_pending_thinking(responses)
                    self._last_thinking_flush_monotonic = now
            # Other delta types (``signature_delta``, ``input_json_delta``)
            # are CLI / tool-dispatch plumbing — not surfaced on the wire.
            return

        if event_type == "content_block_stop":
            index = raw.get("index")
            if not isinstance(index, int):
                return
            block_type = self._block_types_by_index.pop(index, None)
            if block_type == "text":
                self._end_text_if_open(responses)
            elif block_type == "thinking":
                self._end_reasoning_if_open(responses)
            return