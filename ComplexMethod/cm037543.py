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
        The Ernie45 thinking model output format is
            abc\n</think>\n\n<response>\ndef\n</response>\n
        or  abc\n</think>\ndef
        - 'abc' goes to reasoning
        - 'def' goes to content
        """
        # Skip single special tokens
        if len(delta_token_ids) == 1 and (
            delta_token_ids[0]
            in [
                self.start_token_id,
                self.end_token_id,
                self.response_start_token_id,
                self.response_end_token_id,
            ]
        ):
            return None

        # No <think> in previous or delta, also need to check for </think>.
        # Because the model may have generated </think> without <think>
        if self.end_token_id in delta_token_ids:
            # </think> in delta with more tokens,
            # extract reasoning content and content
            think_end_index = delta_text.find(self.end_token)
            reasoning = delta_text[:think_end_index]
            content = delta_text[think_end_index + len(self.end_token) :]
            content = content.lstrip("\n")
            response_start_idx = content.find(self.response_start_token)
            response_end_idx = content.rfind(self.response_end_token)
            if response_start_idx != -1:
                content = content[response_start_idx + len(self.response_start_token) :]
            if response_end_idx != -1:
                content = content[:response_end_idx]
            return DeltaMessage(
                reasoning=reasoning,
                content=content if content else None,
            )
        elif self.end_token_id in previous_token_ids:
            # </think> in previous, thinking content ends
            content = delta_text
            if self.response_start_token_id in delta_token_ids:
                content = content.lstrip("\n")
                response_start_idx = content.find(self.response_start_token)
                content = content[response_start_idx + len(self.response_start_token) :]
                # if have </response>, remove it
                response_end_idx = content.rfind(self.response_end_token)
                if response_end_idx != -1:
                    content = content[:response_end_idx]
            elif self.response_end_token_id in delta_token_ids:
                response_end_idx = content.rfind(self.response_end_token)
                content = content[:response_end_idx]
            # remove \n after </think>  or </response>
            if previous_token_ids[-1] in self.parser_token_ids and (
                len(delta_token_ids) > 0 and delta_token_ids[0] == self.newline_token_id
            ):
                content = content.lstrip("\n")
            # remove \n after </think>\n
            if (
                len(previous_token_ids) > 1
                and previous_token_ids[-2] == self.end_token_id
            ) and (
                len(delta_token_ids) > 0 and delta_token_ids[0] == self.newline_token_id
            ):
                content = content.lstrip("\n")

            return DeltaMessage(content=content if content else None)
        else:
            # no </think> in previous or delta, reasoning content continues
            return DeltaMessage(reasoning=delta_text)