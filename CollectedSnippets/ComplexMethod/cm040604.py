def validate_and_resolve_config(mode, config):
    """Validate and resolve quantization config.

    This function validates the quantization config and resolves the mode.
    If mode is not provided, it is inferred from the config.
    If config is not provided, a default config is inferred from the mode.

    Args:
        mode: Quantization mode.
        config: Quantization config.
    """
    # 1. Backwards Compatibility: Handle string shortcuts.
    if isinstance(config, str):
        mode = config
        config = None

    _validate_mode(mode)

    # 2. Resolve "mode" into a Config object.
    if config is None:
        if mode == "int8":
            config = Int8QuantizationConfig()
        elif mode == "int4":
            config = Int4QuantizationConfig()
        elif mode == "float8":
            config = Float8QuantizationConfig()
        elif mode == "gptq":
            raise ValueError(
                "For GPTQ, you must pass a `GPTQConfig` object in the "
                "`config` argument."
            )
        elif mode == "awq":
            raise ValueError(
                "For AWQ, you must pass an `AWQConfig` object in the "
                "`config` argument."
            )
        else:
            if mode is not None:
                raise ValueError(
                    f"Invalid quantization mode. Received: mode={mode}"
                )
            raise ValueError(
                "You must provide either `mode` or `config` to `quantize`."
            )
    else:
        if not isinstance(config, QuantizationConfig):
            raise ValueError(
                "Argument `config` must be an instance of "
                "`QuantizationConfig`. "
                f"Received: config={config} (of type {type(config)})"
            )

    # 3. Validation: Prevent contradictions.
    if mode is not None and config.mode != mode:
        raise ValueError(
            f"Contradictory arguments: mode='{mode}' but "
            f"config.mode='{config.mode}'"
        )

    # Ensure mode is consistent.
    mode = config.mode

    # Ensure the mode derived from the config is valid.
    _validate_mode(mode)

    if mode == "gptq":
        from keras.src.quantizers.gptq_config import GPTQConfig

        if not isinstance(config, GPTQConfig):
            raise ValueError(
                "Mode 'gptq' requires a valid `config` argument of type "
                f"`GPTQConfig`. Received: {type(config)}"
            )

    if mode == "awq":
        from keras.src.quantizers.awq_config import AWQConfig

        if not isinstance(config, AWQConfig):
            raise ValueError(
                "Mode 'awq' requires a valid `config` argument of type "
                f"`AWQConfig`. Received: {type(config)}"
            )

    return config