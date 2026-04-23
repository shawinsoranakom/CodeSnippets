def _emit_argument_diff(self, raw_args_str: str) -> DeltaMessage | None:
        """Parse raw Gemma4 arguments, convert to JSON, diff, and emit.

        This is the core of the accumulate-then-parse-then-diff strategy:
        1. Parse ``raw_args_str`` with ``_parse_gemma4_args()``
        2. Convert to JSON string with ``json.dumps()``
        3. Withhold trailing closing characters (``"}``) that may move
           as more tokens arrive
        4. Diff against previously streamed JSON and emit only new chars

        **Why withholding is necessary:**

        Gemma4's custom format produces *structurally incomplete* JSON
        during streaming. For example, when ``<|"|>Paris`` arrives
        without a closing delimiter, ``_parse_gemma4_args`` treats it
        as a complete value and produces ``{"location": "Paris"}``. But
        when ``, France<|"|>`` arrives next, the JSON becomes
        ``{"location": "Paris, France"}``. If we had sent the closing
        ``"}`` from the first parse, the concatenated client output
        would be ``{"location": "Paris"}France"}``, which is garbage.

        The solution: **never send trailing closing chars during
        streaming**. They get flushed by ``_handle_tool_call_end()``
        when the ``<tool_call|>`` end marker arrives.

        Args:
            raw_args_str: The raw Gemma4 argument text accumulated so far
                (without the surrounding ``{`` ``}``).

        Returns:
            DeltaMessage with the argument diff, or None if no new content.
        """
        try:
            current_args = _parse_gemma4_args(raw_args_str, partial=True)
        except Exception:
            logger.debug(
                "Could not parse partial Gemma4 args yet: %s",
                raw_args_str[:100],
            )
            return None

        if not current_args:
            return None

        current_args_json = json.dumps(current_args, ensure_ascii=False)

        # Withhold trailing closing characters that may shift as more
        # tokens arrive. Strip trailing '}', '"', ']' and partial
        # STRING_DELIM fragments ('<', '|', '\\', '>') to get the
        # "safe prefix".
        safe_json = current_args_json
        while safe_json and safe_json[-1] in ("}", '"', "]", "<", "|", "\\", ">"):
            safe_json = safe_json[:-1]

        prev_streamed = self.streamed_args_for_tool[self.current_tool_id]

        if not safe_json or safe_json == prev_streamed:
            return None

        # Use find_common_prefix to handle cases where the value changed
        # structurally (e.g., a string grew).
        if prev_streamed:
            prefix = find_common_prefix(prev_streamed, safe_json)
            sent_len = len(prev_streamed)
            prefix_len = len(prefix)

            if prefix_len < sent_len:
                # Structure changed — we sent too much. Truncate our
                # tracking to the common prefix and wait for the final
                # flush in _handle_tool_call_end.
                self.streamed_args_for_tool[self.current_tool_id] = prefix
                return None

            # Stream the new stable portion
            diff = safe_json[sent_len:]
        else:
            # First emission
            diff = safe_json

        if diff:
            self.streamed_args_for_tool[self.current_tool_id] = safe_json
            self.prev_tool_call_arr[self.current_tool_id]["arguments"] = current_args

            return DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=self.current_tool_id,
                        function=DeltaFunctionCall(arguments=diff).model_dump(
                            exclude_none=True
                        ),
                    )
                ]
            )

        return None