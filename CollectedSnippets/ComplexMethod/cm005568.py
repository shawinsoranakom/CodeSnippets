def update_and_check_completion(self, token_id: int, logprob: float | None) -> bool:
        """Update the request with a newly generated token (and optional log probability of the token) and check for
        completion. Returns True if the request is now complete, False otherwise."""
        # Only update if we're in decoding state # TODO: seems useless (always true) -- remove this
        if self.status != RequestStatus.DECODING:
            return False

        # If we're recording timestamps, add timestamp to the list
        if self.record_timestamps:
            self._timestamps.append(time.perf_counter())

        # Stop if we reached an EOS token
        is_eos = token_id in self._eos_token_ids
        current_len = self.generated_len()

        # Replace the temporary token if we're not finishing due to max length
        # (EOS tokens should still be added to the output)
        if is_eos or (current_len < self._new_tokens_limit):
            self.generated_tokens.append(token_id)
            self.tokens_to_process = [token_id]  # this works for 2 levels of pipelines, but not sure for more
            current_len += 1
            if logprob is not None:
                self.logprobs.append(logprob)
        else:
            logger.warning(f"Request {self.request_id} generated a useless token: {token_id}")

        if is_eos or current_len >= self._new_tokens_limit:
            self.status = RequestStatus.FINISHED
            return True
        return False