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
        Extract reasoning content from a delta message.
        Handles streaming output where previous + delta = current.
        Uses token IDs for faster processing.
        """
        # Skip single special tokens
        if len(delta_token_ids) == 1 and (
            delta_token_ids[0] in [self.start_token_id, self.end_token_id]
        ):
            return None

        # Check if start token is present in previous or delta.
        # Keep compatibility with models that don't generate start tokens.
        if self.start_token_id in previous_token_ids:
            if self.end_token_id in delta_token_ids:
                # start token in previous, end token in delta,
                # extract reasoning content
                end_index = delta_text.find(self.end_token)
                reasoning = delta_text[:end_index]
                content = delta_text[end_index + len(self.end_token) :]
                return DeltaMessage(
                    reasoning=reasoning, content=content if content else None
                )
            elif self.end_token_id in previous_token_ids:
                # start token in previous, end token in previous,
                # reasoning content continues
                return DeltaMessage(content=delta_text)
            else:
                # start token in previous, no end token in previous or delta,
                # reasoning content continues
                return DeltaMessage(reasoning=delta_text)
        elif self.start_token_id in delta_token_ids:
            if self.end_token_id in delta_token_ids:
                # start token in delta, end token in delta,
                # extract reasoning content
                start_index = delta_text.find(self.start_token)
                end_index = delta_text.find(self.end_token)
                reasoning = delta_text[start_index + len(self.start_token) : end_index]
                content = delta_text[end_index + len(self.end_token) :]
                return DeltaMessage(
                    reasoning=reasoning, content=content if content else None
                )
            else:
                # start token in delta, no end token in delta,
                # reasoning content continues
                return DeltaMessage(reasoning=delta_text)
        else:
            # not find thinking start token
            return DeltaMessage(content=delta_text)