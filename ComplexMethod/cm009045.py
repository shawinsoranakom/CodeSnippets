def _should_summarize(self, messages: list[AnyMessage], total_tokens: int) -> bool:
        """Determine whether summarization should run for the current token usage."""
        if not self._trigger_conditions:
            return False

        for kind, value in self._trigger_conditions:
            if kind == "messages" and len(messages) >= value:
                return True
            if kind == "tokens" and total_tokens >= value:
                return True
            if kind == "tokens" and self._should_summarize_based_on_reported_tokens(
                messages, value
            ):
                return True
            if kind == "fraction":
                max_input_tokens = self._get_profile_limits()
                if max_input_tokens is None:
                    continue
                threshold = int(max_input_tokens * value)
                if threshold <= 0:
                    threshold = 1
                if total_tokens >= threshold:
                    return True

                if self._should_summarize_based_on_reported_tokens(messages, threshold):
                    return True
        return False