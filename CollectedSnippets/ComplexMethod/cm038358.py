def _extract_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
    ) -> DeltaMessage | None:
        """Tag-counting streaming parser.

        Uses the proven approach from FunctionGemma/Hermes: count start/end
        tags in previous vs current text to determine phase, then
        accumulate-parse-diff for arguments.

        Format: ``<|tool_call>call:name{args}<tool_call|>``
        """
        start_count = current_text.count(self.tool_call_start_token)
        end_count = current_text.count(self.tool_call_end_token)
        prev_start_count = previous_text.count(self.tool_call_start_token)
        prev_end_count = previous_text.count(self.tool_call_end_token)

        # Case 1: Not inside any tool call — emit as content
        if (
            start_count == end_count
            and prev_end_count == end_count
            and self.tool_call_end_token not in delta_text
        ):
            if delta_text:
                return DeltaMessage(content=delta_text)
            return None

        # Case 2: Starting a new tool call
        if start_count > prev_start_count and start_count > end_count:
            self.current_tool_id += 1
            self.current_tool_name_sent = False
            self.streamed_args_for_tool.append("")
            self.prev_tool_call_arr.append({})
            logger.debug("Starting new tool call %d", self.current_tool_id)
            # Don't return yet — fall through to try parsing if there's
            # content after <|tool_call> in this same delta
            # (but usually it's just the token itself, so return None)
            if len(delta_text) <= len(self.tool_call_start_token):
                return None

        # Case 3: Tool call just ended
        if end_count > prev_end_count:
            return self._handle_tool_call_end(current_text)

        # Case 4: In the middle of a tool call — parse partial content
        if start_count > end_count:
            return self._handle_tool_call_middle(current_text)

        # Default: generate text outside tool calls
        if delta_text:
            text = delta_text.replace(self.tool_call_start_token, "")
            text = text.replace(self.tool_call_end_token, "")
            if text:
                return DeltaMessage(content=text)
        return None