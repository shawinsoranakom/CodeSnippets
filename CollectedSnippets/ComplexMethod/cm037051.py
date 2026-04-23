def _validate_logprobs(self, model_config: ModelConfig) -> None:
        max_logprobs = model_config.max_logprobs
        if max_logprobs == -1:
            max_logprobs = model_config.get_vocab_size()

        # Validate sample logprobs.
        if num_logprobs := self.logprobs:
            if num_logprobs == -1:
                num_logprobs = model_config.get_vocab_size()
            if num_logprobs > max_logprobs:
                raise VLLMValidationError(
                    f"Requested sample logprobs of {num_logprobs}, "
                    f"which is greater than max allowed: {max_logprobs}",
                    parameter="logprobs",
                    value=num_logprobs,
                )

        # Validate prompt logprobs.
        if num_prompt_logprobs := self.prompt_logprobs:
            if num_prompt_logprobs == -1:
                num_prompt_logprobs = model_config.get_vocab_size()
            if num_prompt_logprobs > max_logprobs:
                raise VLLMValidationError(
                    f"Requested prompt logprobs of {num_prompt_logprobs}, "
                    f"which is greater than max allowed: {max_logprobs}",
                    parameter="prompt_logprobs",
                    value=num_prompt_logprobs,
                )