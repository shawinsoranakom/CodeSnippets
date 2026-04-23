def feed_chunk(self, chunk: dict) -> list[str]:
        """Process one OpenAI streaming chat.completion.chunk."""
        events: list[str] = []

        # usage-only chunks carry token totals
        usage = chunk.get("usage")
        if usage:
            self._usage = usage

        choices = chunk.get("choices") or []
        if not choices:
            return events

        choice = choices[0]
        delta = choice.get("delta") or {}
        finish_reason = choice.get("finish_reason")

        # ── Text content ──
        content = delta.get("content")
        if content:
            if self._current_block_type != "text":
                if self._current_block_type is not None:
                    events.append(self._close_current_block())
                events.extend(self._open_text_block())
            events.append(
                build_anthropic_sse_event(
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": self.block_index,
                        "delta": {"type": "text_delta", "text": content},
                    },
                )
            )

        # ── Tool calls (streaming deltas) ──
        tool_calls = delta.get("tool_calls") or []
        for tc in tool_calls:
            tc_idx = tc.get("index", 0)
            fn = tc.get("function") or {}
            if tc_idx not in self._tool_call_states:
                # New tool call — close prior block, open tool_use block
                if self._current_block_type is not None:
                    events.append(self._close_current_block())
                tc_id = tc.get("id", "")
                tc_name = fn.get("name", "")
                self.block_index += 1
                self._current_block_type = "tool_use"
                self._tool_call_states[tc_idx] = {
                    "block_index": self.block_index,
                    "id": tc_id,
                    "name": tc_name,
                }
                events.append(
                    build_anthropic_sse_event(
                        "content_block_start",
                        {
                            "type": "content_block_start",
                            "index": self.block_index,
                            "content_block": {
                                "type": "tool_use",
                                "id": tc_id,
                                "name": tc_name,
                                "input": {},
                            },
                        },
                    )
                )

            args_delta = fn.get("arguments", "")
            if args_delta:
                events.append(
                    build_anthropic_sse_event(
                        "content_block_delta",
                        {
                            "type": "content_block_delta",
                            "index": self._tool_call_states[tc_idx]["block_index"],
                            "delta": {
                                "type": "input_json_delta",
                                "partial_json": args_delta,
                            },
                        },
                    )
                )

        # ── Finish reason ──
        if finish_reason:
            if finish_reason == "tool_calls":
                self._stop_reason = "tool_use"
            elif finish_reason == "length":
                self._stop_reason = "max_tokens"
            else:
                self._stop_reason = "end_turn"

        return events