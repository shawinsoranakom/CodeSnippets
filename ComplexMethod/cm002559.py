def _validate_longrope_rope_parameters(self, rope_parameters: dict, ignore_keys: set | None = None):
        required_keys = {"rope_type", "short_factor", "long_factor", "original_max_position_embeddings"}
        optional_keys = {"rope_theta", "attention_factor", "factor"}
        received_keys = set(rope_parameters.keys())
        rope_type = rope_parameters["rope_type"]
        self._check_received_keys(rope_type, received_keys, required_keys, optional_keys, ignore_keys=ignore_keys)

        partial_rotary_factor = rope_parameters.get("partial_rotary_factor", 1.0)
        head_dim = getattr(self, "head_dim", self.hidden_size // self.num_attention_heads)
        dim = int(head_dim * partial_rotary_factor)

        short_factor = rope_parameters.get("short_factor")
        if not (isinstance(short_factor, list) and all(isinstance(x, (int, float)) for x in short_factor)):
            logger.warning(f"`rope_parameters`'s short_factor field must be a list of numbers, got {short_factor}")
        if len(short_factor) != dim // 2:
            logger.warning(
                f"`rope_parameters`'s short_factor field must have length {dim // 2}, got {len(short_factor)}"
            )

        long_factor = rope_parameters.get("long_factor")
        if not (isinstance(long_factor, list) and all(isinstance(x, (int, float)) for x in long_factor)):
            logger.warning(f"`rope_parameters`'s long_factor field must be a list of numbers, got {long_factor}")
        if len(long_factor) != dim // 2:
            logger.warning(
                f"`rope_parameters`'s long_factor field must have length {dim // 2}, got {len(long_factor)}"
            )

        factor = rope_parameters.get("factor")
        original_max_position_embeddings = rope_parameters["original_max_position_embeddings"]

        # Handle Phi3 divergence: we prefer the use of `attention_factor` and/or `factor` over
        # `original_max_position_embeddings` to compute internal variables. The latter is undesirable
        if factor is None and original_max_position_embeddings is not None:
            logger.warning_once(
                "This model config has set a `rope_parameters['original_max_position_embeddings']` field, to be used together with "
                "`max_position_embeddings` to determine a scaling factor. Please set the `factor` field of `rope_parameters`"
                "with this ratio instead -- we recommend the use of this field over `original_max_position_embeddings`, "
                "as it is compatible with most model architectures."
            )
        elif factor is None and original_max_position_embeddings is None:
            logger.warning("Missing required keys in `rope_parameters`: 'factor'")
        elif not isinstance(factor, (float, int)) or factor < 1.0:
            logger.warning(f"`rope_parameters`'s factor field must be a float or int >= 1, got {factor}")

        attention_factor = rope_parameters.get("attention_factor")
        if attention_factor is not None and (not isinstance(attention_factor, (float, int)) or attention_factor < 0.0):
            logger.warning(
                f"`rope_parameters`'s attention_factor field must be a float or int greater than 0, got {attention_factor}"
            )