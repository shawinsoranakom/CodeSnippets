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
        self._update_thinking_state(current_text)

        if self.in_thinking_tag:
            return DeltaMessage(content=delta_text)

        if self._should_buffer_content(delta_text):
            buffered_output = self._process_buffer(delta_text)
            return DeltaMessage(content=buffered_output) if buffered_output else None

        if self._is_end_tool_calls(current_text):
            return DeltaMessage(content=delta_text)

        safe_content, potential_tag = self._split_content_for_buffering(delta_text)
        if potential_tag:
            self.pending_buffer += potential_tag
            return DeltaMessage(content=safe_content) if safe_content else None

        processed_current_text = self.preprocess_model_output(current_text)

        if self.tool_call_start_token not in processed_current_text:
            if (
                self.tool_call_end_token in delta_text
                and self.tool_call_start_token in current_text
            ):
                return None
            if delta_text.strip() == "" and self.tool_call_start_token in current_text:
                return None
            if (
                self._get_current_tool_index() != -1
                and self.tool_call_end_token in current_text
            ):
                self._reset_streaming_state()
            return DeltaMessage(content=delta_text)

        if (
            self.tool_call_start_token_id is not None
            and self.tool_call_start_token_id in delta_token_ids
            and len(delta_token_ids) == 1
        ):
            return None

        original_tool_start = self._find_tool_start_outside_thinking(current_text)
        if original_tool_start is None:
            return None

        content_before_tools = self._extract_content_before_tools(
            current_text, delta_text, original_tool_start
        )
        if content_before_tools:
            return DeltaMessage(content=content_before_tools)

        try:
            tool_content = self._extract_tool_content(current_text, original_tool_start)
            current_tools_count = self._detect_tools_in_text(tool_content)

            if current_tools_count == 0:
                return None

            if self._get_current_tool_index() == -1:
                self._reset_streaming_state()

            self._ensure_state_arrays(current_tools_count)

            return self._handle_tool_name_streaming(
                tool_content, current_tools_count
            ) or self._handle_tool_args_streaming(tool_content, current_tools_count)

        except Exception:
            logger.exception(
                "An unexpected error occurred ", "during streaming tool call handling."
            )
            return None