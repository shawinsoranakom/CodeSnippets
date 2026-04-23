def extract_reasoning_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
    ) -> DeltaMessage | None:
        """
        Extract reasoning content from a delta message during streaming.
        """
        if self._identity_parser is not None:
            return self._identity_parser.extract_reasoning_streaming(
                previous_text,
                current_text,
                delta_text,
                previous_token_ids,
                current_token_ids,
                delta_token_ids,
            )

        # If reasoning has already ended in previous tokens, this is content
        if self.is_reasoning_end(previous_token_ids):
            return DeltaMessage(content=delta_text)

        # Skip single special tokens
        if len(delta_token_ids) == 1 and delta_token_ids[0] in [
            self._start_token_id,
            self._end_token_id,
        ]:
            return None

        if self._end_token_id in delta_token_ids:
            end_index = delta_text.find(self._end_token)
            reasoning = delta_text[:end_index]
            content = delta_text[end_index + len(self._end_token) :]
            return DeltaMessage(
                reasoning=reasoning, content=content if content else None
            )

        if self._tool_section_start_token_id in delta_token_ids:
            tool_index = delta_text.find(self._tool_section_start_token)
            reasoning = delta_text[:tool_index]
            content = delta_text[tool_index:]
            return DeltaMessage(reasoning=reasoning, content=content)

        # still reasoning (no end token)
        return DeltaMessage(reasoning=delta_text)