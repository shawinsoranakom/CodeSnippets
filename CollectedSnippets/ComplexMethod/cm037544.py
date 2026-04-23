def _get_delta_message_with_no_response_bounds(
        self,
        current_text: str,
        reasoning: str,
        delta_text: str,
    ) -> DeltaMessage:
        """Parse the delta message when the current text has both reasoning
        content with no (response) content. NOTE that we may have overlapping
        tokens with the start of reasoning / start of response sequences on
        either side of the delta text.

        Args:
            current_text (str): The full previous + delta text.
            reasoning (str): reasoning content from current_text.
            delta_text (str): Text to consider and parse content from.

        Returns:
            DeltaMessage: Message containing the parsed content.
        """
        # If we have no reasoning content or explicitly end with the start of
        # response sequence, we are in transition to the response; need to be
        # careful here, since the final token (:) will match the reasoning
        # content and fully parse it out; we should not pass the : back.
        ends_with_start_response_seq = any(
            current_text.endswith(response_start)
            for response_start in self.valid_response_starts
        )
        if reasoning is None or ends_with_start_response_seq:
            return DeltaMessage(reasoning=None, content=None)

        # Consider previous / current text only within context of the reasoning
        previous_text = reasoning[: -len(delta_text)]
        current_text = reasoning

        # We need to be careful about adding unfinished response sequences;
        # Find the place at which we MIGHT be starting a response sequence
        prev_idx = previous_text.rfind(self.seq_boundary_start)
        delta_idx = delta_text.rfind(self.seq_boundary_start)

        # Check the state of potential start of response substring matches.
        prev_was_substr = (
            self._is_response_start_substr(previous_text[prev_idx:])
            if prev_idx >= 0
            else False
        )
        delta_continues_substr = (
            self._is_response_start_substr(current_text[prev_idx:])
            if prev_idx >= 0
            else False
        )
        delta_new_substr = (
            self._is_response_start_substr(delta_text[delta_idx:])
            if delta_idx >= 0
            else False
        )

        # Delta only contains potential continued response sequence text.
        if delta_continues_substr:
            return DeltaMessage(reasoning=None, content=None)

        if not prev_was_substr:
            # Delta may be starting a new response seq but has other text too.
            if delta_new_substr:
                return DeltaMessage(reasoning=delta_text[:delta_idx], content=None)
            # Normal case for most reasoning text (no potential special seqs).
            return DeltaMessage(reasoning=delta_text, content=None)
        # The substring that previously seemed to be a potential response
        # seq wasn't one; we need to add the content to the delta message,
        # and also slice off the potential response sequence
        elif delta_new_substr:
            reasoning = previous_text[prev_idx:] + delta_text[:delta_idx]
            return DeltaMessage(reasoning=reasoning, content=None)
        # No new substring yet, and we broke our old one; take the whole delta
        return DeltaMessage(
            reasoning=previous_text[prev_idx:] + delta_text,
            content=None,
        )