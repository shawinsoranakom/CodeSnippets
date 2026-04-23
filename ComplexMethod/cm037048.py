def _verify_args(self) -> None:
        if not isinstance(self.n, int):
            raise ValueError(f"n must be an int, but is of type {type(self.n)}")
        if self.n < 1:
            raise ValueError(f"n must be at least 1, got {self.n}.")
        max_n = envs.VLLM_MAX_N_SEQUENCES
        if self.n > max_n:
            raise ValueError(
                f"n must be at most {max_n}, got {self.n}. "
                "To increase this limit, set the VLLM_MAX_N_SEQUENCES "
                "environment variable."
            )
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError(
                f"presence_penalty must be in [-2, 2], got {self.presence_penalty}."
            )
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError(
                f"frequency_penalty must be in [-2, 2], got {self.frequency_penalty}."
            )
        if self.repetition_penalty <= 0.0:
            raise ValueError(
                "repetition_penalty must be greater than zero, got "
                f"{self.repetition_penalty}."
            )
        if self.temperature < 0.0:
            raise VLLMValidationError(
                f"temperature must be non-negative, got {self.temperature}.",
                parameter="temperature",
                value=self.temperature,
            )
        if not 0.0 < self.top_p <= 1.0:
            raise VLLMValidationError(
                f"top_p must be in (0, 1], got {self.top_p}.",
                parameter="top_p",
                value=self.top_p,
            )
        # quietly accept -1 as disabled, but prefer 0
        if self.top_k < -1:
            raise ValueError(
                f"top_k must be 0 (disable), or at least 1, got {self.top_k}."
            )
        if not isinstance(self.top_k, int):
            raise TypeError(
                f"top_k must be an integer, got {type(self.top_k).__name__}"
            )
        if not 0.0 <= self.min_p <= 1.0:
            raise ValueError(f"min_p must be in [0, 1], got {self.min_p}.")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise VLLMValidationError(
                f"max_tokens must be at least 1, got {self.max_tokens}.",
                parameter="max_tokens",
                value=self.max_tokens,
            )
        if self.min_tokens < 0:
            raise ValueError(
                f"min_tokens must be greater than or equal to 0, got {self.min_tokens}."
            )
        if self.max_tokens is not None and self.min_tokens > self.max_tokens:
            raise ValueError(
                f"min_tokens must be less than or equal to "
                f"max_tokens={self.max_tokens}, got {self.min_tokens}."
            )
        if self.logprobs is not None and self.logprobs != -1 and self.logprobs < 0:
            raise VLLMValidationError(
                f"logprobs must be non-negative or -1, got {self.logprobs}.",
                parameter="logprobs",
                value=self.logprobs,
            )
        if (
            self.prompt_logprobs is not None
            and self.prompt_logprobs != -1
            and self.prompt_logprobs < 0
        ):
            raise VLLMValidationError(
                f"prompt_logprobs must be non-negative or -1, got "
                f"{self.prompt_logprobs}.",
                parameter="prompt_logprobs",
                value=self.prompt_logprobs,
            )
        assert isinstance(self.stop_token_ids, list)
        if not all(isinstance(st_id, int) for st_id in self.stop_token_ids):
            raise ValueError(
                f"stop_token_ids must contain only integers, got {self.stop_token_ids}."
            )
        assert isinstance(self.stop, list)
        if any(not stop_str for stop_str in self.stop):
            raise ValueError("stop cannot contain an empty string.")
        if self.stop and not self.detokenize:
            raise ValueError(
                "stop strings are only supported when detokenize is True. "
                "Set detokenize=True to use stop."
            )