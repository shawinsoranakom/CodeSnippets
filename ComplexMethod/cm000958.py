def on_delta(self, delta: ChoiceDelta) -> list[StreamBaseResponse]:
        """Return events for the reasoning text carried by *delta*.

        Empty list when the chunk carries no reasoning payload, so this is
        safe to call on every chunk without guarding at the call site.

        Persistence (when a session message list is attached) stays
        per-delta so the DB row's content always equals the concatenation
        of wire deltas at every chunk boundary, independent of the
        coalescing window.  Only the wire emission is batched.
        """
        ext = OpenRouterDeltaExtension.from_delta(delta)
        text = ext.visible_text()
        if not text:
            return []
        events: list[StreamBaseResponse] = []
        # First reasoning text in this block — emit Start + the first Delta
        # atomically so the frontend Reasoning collapse renders immediately
        # rather than waiting for the coalesce window to elapse.  Subsequent
        # chunks buffer into ``_pending_delta`` and only flush when the
        # char/time thresholds trip.
        # Sample the monotonic clock exactly once per chunk — at ~4,700
        # chunks per turn, folding the two calls into one cuts ~4,700
        # syscalls off the hot path without changing semantics.
        now = time.monotonic()
        if not self._open:
            if self._render_in_ui:
                events.append(StreamReasoningStart(id=self._block_id))
                events.append(StreamReasoningDelta(id=self._block_id, delta=text))
            self._open = True
            self._last_flush_monotonic = now
            if self._session_messages is not None:
                self._current_row = ChatMessage(role="reasoning", content=text)
                self._session_messages.append(self._current_row)
            return events

        if self._current_row is not None:
            self._current_row.content = (self._current_row.content or "") + text

        self._pending_delta += text
        if self._should_flush_pending(now):
            if self._render_in_ui:
                events.append(
                    StreamReasoningDelta(id=self._block_id, delta=self._pending_delta)
                )
            self._pending_delta = ""
            self._last_flush_monotonic = now
        return events