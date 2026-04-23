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
        Extract reasoning content from a streaming delta.

        Since <think> is placed in the prompt by the chat template, all
        generated tokens before </think> are reasoning and tokens after
        are content.

        NOTE: When thinking is disabled, no think tokens appear in the
        generated output. The serving layer detects this via
        prompt_is_reasoning_end and routes deltas as content without
        calling this method.
        """
        # Strip <think> from delta if present (old template / edge case
        # where the model generates <think> itself).
        if self.start_token_id in delta_token_ids:
            start_idx = delta_text.find(self.start_token)
            if start_idx >= 0:
                delta_text = delta_text[start_idx + len(self.start_token) :]

        if self.end_token_id in delta_token_ids:
            # End token in this delta: split reasoning from content.
            end_index = delta_text.find(self.end_token)
            if end_index >= 0:
                reasoning = delta_text[:end_index]
                content = delta_text[end_index + len(self.end_token) :]
                if not reasoning and not content:
                    return None
                return DeltaMessage(
                    reasoning=reasoning if reasoning else None,
                    content=content if content else None,
                )
            # end_token_id in IDs but not in text (already stripped)
            return None

        # No end token in this delta.
        if not delta_text:
            # Nothing left after stripping start token.
            return None
        elif self.end_token_id in previous_token_ids:
            # End token already passed: everything is content now.
            return DeltaMessage(content=delta_text)
        else:
            # No end token yet: still in reasoning phase.
            return DeltaMessage(reasoning=delta_text)