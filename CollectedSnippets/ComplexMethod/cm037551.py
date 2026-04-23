def _is_reasoning_end_from_ids(self, input_ids: Sequence[int]) -> bool:
        # Scan backwards to find the last special token, <think> or </think>.
        last_special = None
        last_idx = -1
        for i in range(len(input_ids) - 1, -1, -1):
            token_id = input_ids[i]
            if token_id == self.start_token_id:
                last_special = "start"
                last_idx = i
                break
            if token_id == self.end_token_id:
                last_special = "end"
                last_idx = i
                break

        if last_special == "start":
            # If we're already waiting for one token after </think>, do not
            # clear the pending state just because the prompt contains <think>.
            # Streaming deltas should not include <think> for this model.
            if self._end_token_pending:
                return False
            # A start token after any end token means reasoning is ongoing.
            self._end_token_pending = False
            return False

        if last_special == "end":
            # Require at least one token after </think> before ending.
            if last_idx < len(input_ids) - 1:
                self._end_token_pending = False
                return True
            self._end_token_pending = True
            return False

        # No special tokens in this input. If we were waiting for one token
        # after </think>, any new token completes the end.
        if self._end_token_pending and input_ids:
            self._end_token_pending = False
            return True

        return False