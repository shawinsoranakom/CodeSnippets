def _get_and_verify_max_len(
    hf_config: PretrainedConfig,
    model_arch_config: ModelArchitectureConfig,
    tokenizer_config: dict | None,
    max_model_len: int | None,
    disable_sliding_window: bool,
    sliding_window: int | None,
    spec_target_max_model_len: int | None = None,
    encoder_config: dict[str, Any] | None = None,
) -> int:
    """Get and verify the model's maximum length."""
    (derived_max_model_len, max_len_key) = (
        model_arch_config.derived_max_model_len_and_key
    )

    # If sliding window is manually disabled, max_length should be less
    # than the sliding window length in the model config.
    if (
        disable_sliding_window
        and sliding_window is not None
        and sliding_window < derived_max_model_len
    ):
        max_len_key = "sliding_window"
        derived_max_model_len = sliding_window

    # Consider model_max_length in tokenizer_config
    if tokenizer_config:
        tokenizer_model_max_length = tokenizer_config.get(
            "model_max_length", derived_max_model_len
        )
        derived_max_model_len = min(derived_max_model_len, tokenizer_model_max_length)

    # If none of the keys were found in the config, use a default and
    # log a warning.
    if derived_max_model_len == float("inf"):
        if max_model_len is not None:
            # If max_model_len is specified, we use it.
            return max_model_len

        if spec_target_max_model_len is not None:
            # If this is a speculative draft model, we use the max model len
            # from the target model.
            return spec_target_max_model_len

        default_max_len = 2048
        logger.warning(
            "The model's config.json does not contain any of the keys "
            "to determine the original maximum length of the model. "
            "Assuming the model's maximum length is %d.",
            default_max_len,
        )
        derived_max_model_len = default_max_len

    # In Transformers v5 rope_parameters could be TypedDict or dict[str, TypedDict].
    # To simplify the verification, we convert it to dict[str, TypedDict].
    rope_parameters = getattr(hf_config, "rope_parameters", None)
    if rope_parameters and not is_rope_parameters_nested(rope_parameters):
        rope_parameters = {"": rope_parameters}

    # NOTE(woosuk): Gemma3's max_model_len (128K) is already scaled by RoPE
    # scaling, so we skip applying the scaling factor again.
    if rope_parameters is not None and "gemma3" not in hf_config.model_type:
        scaling_factor = 1.0
        for rp in rope_parameters.values():
            # No need to consider "type" key because of patch_rope_parameters when
            # loading HF config
            rope_type = rp["rope_type"]

            if rope_type not in ("su", "longrope", "llama3"):
                # NOTE: rope_type == "default" does not define factor https://github.com/huggingface/transformers/blob/v4.45.2/src/transformers/modeling_rope_utils.py
                # NOTE: This assumes all layer types have the same scaling factor.
                scaling_factor = rp.get("factor", scaling_factor)

                if rope_type == "yarn":
                    derived_max_model_len = rp["original_max_position_embeddings"]
        if scaling_factor is None:
            # Fallback the factor to 1.0 if a user assigned `null`
            logger.warning_once(
                "The model's RoPE configuration has a null scaling "
                "factor which is unexpected. This likely indicates a bug "
                "in the model's HuggingFace config.json. Please notify the "
                "model vendor. Falling back the value to 1.0. "
            )
            scaling_factor = 1.0
        # Do this outside loop since all layer types should have the same scaling
        derived_max_model_len *= scaling_factor

    if encoder_config and "max_seq_length" in encoder_config:
        derived_max_model_len = encoder_config["max_seq_length"]

    # If the user didn't specify `max_model_len` or specified -1 (auto-fit),
    # then use that derived from the model config as a default value.
    # When -1 is specified, the engine will later auto-fit to available memory.
    if max_model_len is None or max_model_len == -1:
        # For LongRoPE, default to original_max_position_embeddings to avoid
        # performance degradation for shorter sequences
        if rope_parameters is not None and any(
            rp["rope_type"] == "longrope" for rp in rope_parameters.values()
        ):
            max_model_len = int(
                getattr(
                    hf_config, "original_max_position_embeddings", derived_max_model_len
                )
            )
        else:
            max_model_len = int(derived_max_model_len)
        max_model_len = current_platform.check_max_model_len(max_model_len)

    # If the user specified a max length, make sure it is smaller than the
    # derived length from the HF model config.
    elif max_model_len > derived_max_model_len:
        # Some models might have a separate key for specifying model_max_length
        # that will be bigger than derived_max_model_len. We compare user input
        # with model_max_length and allow this override when it's smaller.
        model_max_length = getattr(hf_config, "model_max_length", None)
        if model_max_length is None or max_model_len > model_max_length:
            msg = (
                f"User-specified max_model_len ({max_model_len}) is greater "
                f"than the derived max_model_len ({max_len_key}="
                f"{derived_max_model_len} or model_max_length="
                f"{model_max_length} in model's config.json)."
            )
            warning = (
                "VLLM_ALLOW_LONG_MAX_MODEL_LEN must be used with extreme "
                "caution. If the model uses relative position encoding (RoPE), "
                "positions exceeding derived_max_model_len lead to nan. If the "
                "model uses absolute position encoding, positions exceeding "
                "derived_max_model_len will cause a CUDA array out-of-bounds "
                "error."
            )
            if envs.VLLM_ALLOW_LONG_MAX_MODEL_LEN:
                logger.warning_once("%s %s", msg, warning)
            else:
                raise ValueError(
                    f"{msg} To allow overriding this maximum, set "
                    f"the env var VLLM_ALLOW_LONG_MAX_MODEL_LEN=1. {warning}"
                )
    return int(max_model_len)