def _validate_yarn_rope_parameters(self, rope_parameters: dict, ignore_keys: set | None = None):
        required_keys = {"rope_type", "factor", "original_max_position_embeddings"}
        optional_keys = {
            "rope_theta",
            "attention_factor",
            "beta_fast",
            "beta_slow",
            "mscale",
            "mscale_all_dim",
            "truncate",
        }
        received_keys = set(rope_parameters.keys())
        rope_type = rope_parameters["rope_type"]
        self._check_received_keys(rope_type, received_keys, required_keys, optional_keys, ignore_keys=ignore_keys)

        factor = rope_parameters["factor"]
        if factor is None or not isinstance(factor, (float, int)) or factor < 1.0:
            logger.warning(f"`rope_parameters`'s factor field must be a float or int >= 1, got {factor}")

        attention_factor = rope_parameters.get("attention_factor")
        if attention_factor is not None and (not isinstance(attention_factor, float) or attention_factor < 0):
            logger.warning(
                f"`rope_parameters`'s attention_factor field must be a float greater than 0, got {attention_factor}"
            )
        beta_fast = rope_parameters.get("beta_fast")
        if beta_fast is not None and not isinstance(beta_fast, (float, int)):
            logger.warning(f"`rope_parameters`'s beta_fast field must be a float or int, got {beta_fast}")
        beta_slow = rope_parameters.get("beta_slow")
        if beta_slow is not None and not isinstance(beta_slow, (float, int)):
            logger.warning(f"`rope_parameters`'s beta_slow field must be a float or int, got {beta_slow}")

        if (beta_fast or 32) < (beta_slow or 1):
            logger.warning(
                f"`rope_parameters`'s beta_fast field must be greater than beta_slow, got beta_fast={beta_fast} "
                f"(defaults to 32 if None) and beta_slow={beta_slow} (defaults to 1 if None)"
            )

        # Double-check: `factor` should be the ratio between the pre-yarn and post-yarn context lengths.
        # NOTE: we might get `implicit_factor == 1` if config's `original_max_position_embeddings` was
        # inferred from `max_position_embeddings` during standardization
        original_max_position_embeddings = self.rope_parameters["original_max_position_embeddings"]
        implicit_factor = self.max_position_embeddings / original_max_position_embeddings
        if implicit_factor != factor and implicit_factor != 1:
            logger.warning_once(
                f"The explicitly set RoPE scaling factor (config.rope_parameters['factor'] = {factor}) does not match "
                "the ratio implicitly set by other parameters (implicit factor = "
                "post-yarn context length / pre-yarn context length = "
                "config.max_position_embeddings / config.rope_parameters['original_max_position_embeddings'] = "
                f"{implicit_factor}). Using the explicit factor ({factor}) in YaRN. This may cause unexpected "
                "behaviour in model usage, please correct the 'original_max_position_embeddings' fields in the model config."
            )