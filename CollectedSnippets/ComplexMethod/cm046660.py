def _process_incremental(self, raw: str) -> None:
        """Parse harmony channels and emit deltas per-channel.

        Instead of transforming the entire raw text and computing a string
        delta (which breaks when wrapping ``<think>`` tags shift position),
        this tracks per-channel content lengths and emits:

        - ``<think>`` once when analysis channel first appears
        - analysis content deltas (computed on channel content directly)
        - ``</think>`` once when final channel first appears
        - final content deltas
        """
        # If raw contains <|channel|> but no complete channel+message pair yet,
        # buffer silently — don't emit partial channel names as text.
        has_channel_token = "<|channel|>" in raw
        matches = list(self._HARMONY_RE.finditer(raw))

        if has_channel_token and not matches:
            # Partial harmony markup still building — wait for more tokens
            return

        if not has_channel_token and not matches:
            # No harmony protocol at all — should not happen for gpt-oss
            # but handle gracefully by not emitting anything
            return

        for m in matches:
            channel = m.group(1).lower()
            content = m.group(2)

            if channel == "analysis":
                if not self._emitted_think_open:
                    self._queue.put("<think>")
                    self._emitted_think_open = True

                new_content = content[self._analysis_emitted :]
                if new_content:
                    self._analysis_emitted = len(content)
                    self._queue.put(new_content)

            elif channel in ("final", "assistant"):
                if self._emitted_think_open and not self._emitted_think_close:
                    self._queue.put("</think>")
                    self._emitted_think_close = True

                new_content = content[self._final_emitted :]
                if new_content:
                    self._final_emitted = len(content)
                    self._queue.put(new_content)