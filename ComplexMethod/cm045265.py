def _create_args_from_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    if "response_format" in config:
        warnings.warn(
            "Using response_format will be deprecated. Use json_output instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    create_args: Dict[str, Any] = {}
    options_dict: Dict[str, Any] = {}

    if "options" in config:
        if isinstance(config["options"], Mapping):
            options_map: Mapping[str, Any] = config["options"]
            options_dict = dict(options_map)
        else:
            options_dict = {}

    for k, v in config.items():
        k_lower = k.lower()
        if k_lower in OLLAMA_VALID_CREATE_KWARGS_KEYS:
            create_args[k_lower] = v
        elif k_lower in LLM_CONTROL_PARAMS:
            options_dict[k_lower] = v
            trace_logger.info(f"Moving LLM control parameter '{k}' to options dict")
        else:
            trace_logger.info(f"Dropped unrecognized key from create_args: {k}")

    if options_dict:
        create_args["options"] = options_dict

    return create_args