def _verify_args(self) -> Self:
        if self.tensor_parallel_size is not None:
            raise ValueError(
                "'tensor_parallel_size' is not a valid argument in the "
                "speculative_config. Please pass 'draft_tensor_parallel_size' instead."
            )

        if self.num_speculative_tokens is None:
            raise ValueError(
                "num_speculative_tokens must be provided with "
                "speculative model unless the draft model config contains an "
                "n_predict parameter."
            )

        if self.num_speculative_tokens <= 0:
            raise ValueError(
                "Expected num_speculative_tokens to be greater "
                f"than zero ({self.num_speculative_tokens})."
            )

        if self.draft_model_config:
            self.draft_model_config.verify_with_parallel_config(
                self.draft_parallel_config
            )

        aux_hidden_states_supported = [
            "llama",
            "qwen",
            "minicpm",
            "gpt_oss",
            "hunyuan_vl",
            "hunyuan_v1_dense",
            "afmoe",
            "nemotron_h",
            "deepseek_v2",
            "deepseek_v3",
            "kimi_k2",
            "kimi_k25",
            "minimax_m2",
            "gemma4",
        ]
        if (
            self.method in ("eagle3", "extract_hidden_states", "dflash")
            and self.target_model_config
            and not any(
                supported_model in self.target_model_config.hf_text_config.model_type
                for supported_model in aux_hidden_states_supported
            )
        ):
            raise ValueError(
                f"{self.method} is only supported for {aux_hidden_states_supported}"
                f" models. Got {self.target_model_config.hf_text_config.model_type=}"
            )
        self.verify_equal_vocab_size_if_draft_model()
        return self