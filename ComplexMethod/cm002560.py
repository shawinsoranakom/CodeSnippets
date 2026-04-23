def _validate_llama3_rope_parameters(self, rope_parameters: dict, ignore_keys: set | None = None):
        required_keys = {
            "rope_type",
            "factor",
            "original_max_position_embeddings",
            "low_freq_factor",
            "high_freq_factor",
            "rope_theta",
        }
        rope_type = rope_parameters["rope_type"]
        received_keys = set(rope_parameters.keys())
        self._check_received_keys(rope_type, received_keys, required_keys, ignore_keys=ignore_keys)

        factor = rope_parameters["factor"]
        if factor is None or not isinstance(factor, (float, int)) or factor < 1.0:
            logger.warning(f"`rope_parameters`'s factor field must be a float or int >= 1, got {factor}")

        low_freq_factor = rope_parameters["low_freq_factor"]
        high_freq_factor = rope_parameters["high_freq_factor"]
        if low_freq_factor is None or not isinstance(low_freq_factor, (float, int)):
            logger.warning(f"`rope_parameters`'s low_freq_factor field must be a float, or int got {low_freq_factor}")
        if high_freq_factor is None or not isinstance(high_freq_factor, (float, int)):
            logger.warning(
                f"`rope_parameters`'s high_freq_factor field must be a float or int, got {high_freq_factor}"
            )
        if high_freq_factor <= low_freq_factor:
            logger.warning(
                "`rope_parameters`'s high_freq_factor field must be greater than low_freq_factor, got high_freq_factor="
                f"{high_freq_factor} and low_freq_factor={low_freq_factor}"
            )

        original_max_position_embeddings = rope_parameters["original_max_position_embeddings"]
        if original_max_position_embeddings is None or not isinstance(original_max_position_embeddings, int):
            logger.warning(
                "`rope_parameters`'s original_max_position_embeddings field must be an integer, got "
                f"{original_max_position_embeddings}"
            )
        if original_max_position_embeddings >= self.max_position_embeddings:
            logger.warning(
                "`rope_parameters`'s original_max_position_embeddings field must be less than max_position_embeddings, got "
                f"{original_max_position_embeddings} and max_position_embeddings={self.max_position_embeddings}"
            )