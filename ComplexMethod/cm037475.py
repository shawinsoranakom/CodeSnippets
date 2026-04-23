def _validate_prompt_len(
        self,
        prompt_len: int,
        prompt_type: Literal["encoder", "decoder"],
    ):
        if self.skip_prompt_length_check:
            return

        if prompt_len == 0 and prompt_type == "decoder":
            raise ValueError(f"The {prompt_type} prompt cannot be empty")

        model_config = self.model_config
        max_prompt_len = (
            model_config.max_model_len
            if prompt_type == "decoder"
            else self.mm_encoder_cache_size
        )
        if prompt_len > max_prompt_len:
            if self.supports_mm_inputs:
                suggestion = (
                    "Make sure that `max_model_len` is no smaller than the "
                    "number of text tokens plus multimodal tokens. For image "
                    "inputs, the number of image tokens depends on the number "
                    "of images, and possibly their aspect ratios as well."
                )
            else:
                suggestion = (
                    "Make sure that `max_model_len` is no smaller than the "
                    "number of text tokens."
                )

            raise ValueError(
                f"The {prompt_type} prompt (length {prompt_len}) is "
                f"longer than the maximum model length of {max_prompt_len}. "
                f"{suggestion}"
            )
        elif prompt_len == max_prompt_len and model_config.runner_type == "generate":
            suggestion = (
                "Make sure that `max_model_len` is no smaller than the "
                "number of text tokens (prompt + requested output tokens)."
            )
            raise ValueError(
                f"The {prompt_type} prompt (length {prompt_len}) plus the number of "
                f"requested output tokens (at least 1) is longer than the maximum "
                f"model length of {max_prompt_len}. {suggestion}"
            )