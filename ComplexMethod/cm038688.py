def verify_max_model_len(self, max_model_len: int) -> Self:
        if (
            self.max_num_batched_tokens < max_model_len
            and not self.enable_chunked_prefill
        ):
            raise ValueError(
                f"max_num_batched_tokens ({self.max_num_batched_tokens}) is "
                f"smaller than max_model_len ({max_model_len}). "
                "This effectively limits the maximum sequence length to "
                "max_num_batched_tokens and makes vLLM reject longer "
                "sequences. Please increase max_num_batched_tokens or "
                "decrease max_model_len."
            )

        if self.max_num_batched_tokens < self.max_num_seqs:
            raise ValueError(
                f"max_num_batched_tokens ({self.max_num_batched_tokens}) must "
                "be greater than or equal to max_num_seqs "
                f"({self.max_num_seqs})."
            )

        if self.max_num_batched_tokens > self.max_num_seqs * max_model_len:
            logger.warning(
                "max_num_batched_tokens (%d) exceeds max_num_seqs "
                "* max_model_len (%d). This may lead to unexpected behavior.",
                self.max_num_batched_tokens,
                self.max_num_seqs * max_model_len,
            )

        if self.max_num_partial_prefills > 1:
            if not self.enable_chunked_prefill:
                raise ValueError(
                    "Chunked prefill must be enabled to set "
                    "max_num_partial_prefills > 1."
                )

            if self.long_prefill_token_threshold > max_model_len:
                raise ValueError(
                    "long_prefill_token_threshold "
                    f"({self.long_prefill_token_threshold}) cannot be greater "
                    f"than the max_model_len ({max_model_len})."
                )

        if self.max_long_partial_prefills > self.max_num_partial_prefills:
            raise ValueError(
                f"{self.max_long_partial_prefills=} must be less than or equal to "
                f"{self.max_num_partial_prefills=}."
            )

        return self