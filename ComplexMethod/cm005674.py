def record_batch_metrics(self, future_states: list) -> None:
        """Record metrics about the batch composition including decode/prefill ratio and batch fill percentage.

        Args:
            requests_in_batch: List of request states in the current batch
        """
        if not _has_opentelemetry or not future_states:
            return

        decode_tokens = 0
        prefill_tokens = 0

        for future_state in future_states:
            state = future_state.state
            if state.status == RequestStatus.DECODING:
                decode_tokens += 1
            elif state.status in [RequestStatus.PREFILLING, RequestStatus.PREFILLING_SPLIT]:
                prefill_tokens += len(state.prompt_ids)

        total_batch_tokens = decode_tokens + prefill_tokens

        try:
            if prefill_tokens > 0:
                self.prefill_tokens_counter.add(prefill_tokens)

            if decode_tokens > 0:
                self.decode_tokens_counter.add(decode_tokens)

            if prefill_tokens > 0:
                ratio = decode_tokens / prefill_tokens
                self.decode_prefill_ratio_gauge.set(ratio)

            fill_percentage = (total_batch_tokens / self.max_batch_tokens) * 100.0
            self.batch_fill_percentage_histogram.record(fill_percentage)
            logger.debug(
                f"Batch metrics: {decode_tokens} decode tokens, {prefill_tokens} prefill tokens, "
                f"batch fill: {fill_percentage:.2f}% ({total_batch_tokens}/{self.max_batch_tokens})"
            )
        except Exception as e:
            logger.warning(f"Failed to record batch metrics: {e}")