def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        """Incrementally stream tool call deltas from accumulated output.

        On each invocation, re-parses the full ``current_text`` to find
        ``<tool_call>`` regions, then diffs against previously sent state
        to emit only new content, tool names, or argument fragments.

        Returns a ``DeltaMessage`` containing either plain content (for
        text preceding any tool call) or one or more ``DeltaToolCall``
        entries, or ``None`` if there is nothing new to send yet."""
        try:
            # Extract any content before tool calls.
            content = self._extract_content(current_text)
            tool_call_jsons = self._extract_tool_call_jsons(current_text)
            tool_call_deltas: list[DeltaToolCall] = []

            for i, (tc_json, is_complete) in enumerate(tool_call_jsons):
                if i >= len(self.prev_tool_call_arr):
                    self.prev_tool_call_arr.append({})
                    self.streamed_args_for_tool.append("")

                # Stream back tool name.
                if "name" not in self.prev_tool_call_arr[i]:
                    name = self._extract_tool_name(tc_json)
                    if not name:
                        # Can't skip to tool i+1 if i isn't ready
                        break
                    self.prev_tool_call_arr[i]["name"] = name
                    tool_call_deltas.append(
                        DeltaToolCall(
                            index=i,
                            type="function",
                            id=make_tool_call_id(),
                            function=DeltaFunctionCall(name=name).model_dump(
                                exclude_none=True
                            ),
                        )
                    )

                # Stream back new tool args by diffing against what was sent.
                args_diff = self._compute_args_diff(i, tc_json, is_complete)
                if args_diff:
                    tool_call_deltas.append(
                        DeltaToolCall(
                            index=i,
                            function=DeltaFunctionCall(arguments=args_diff).model_dump(
                                exclude_none=True
                            ),
                        )
                    )

            if content or tool_call_deltas:
                return DeltaMessage(
                    content=content,
                    tool_calls=tool_call_deltas,
                )

            return None

        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
            return None