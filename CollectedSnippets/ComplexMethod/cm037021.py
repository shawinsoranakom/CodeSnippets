def _configure_vllm_root_logger() -> None:
    logging_config: dict[str, dict[str, Any] | Any] = {}

    if not envs.VLLM_CONFIGURE_LOGGING and envs.VLLM_LOGGING_CONFIG_PATH:
        raise RuntimeError(
            "VLLM_CONFIGURE_LOGGING evaluated to false, but "
            "VLLM_LOGGING_CONFIG_PATH was given. VLLM_LOGGING_CONFIG_PATH "
            "implies VLLM_CONFIGURE_LOGGING. Please enable "
            "VLLM_CONFIGURE_LOGGING or unset VLLM_LOGGING_CONFIG_PATH."
        )

    if envs.VLLM_CONFIGURE_LOGGING:
        logging_config = DEFAULT_LOGGING_CONFIG

        vllm_handler = logging_config["handlers"]["vllm"]
        # Refresh these values in case env vars have changed.
        vllm_handler["level"] = envs.VLLM_LOGGING_LEVEL
        vllm_handler["stream"] = envs.VLLM_LOGGING_STREAM
        vllm_handler["formatter"] = "vllm_color" if _use_color() else "vllm"

        vllm_loggers = logging_config["loggers"]["vllm"]
        vllm_loggers["level"] = envs.VLLM_LOGGING_LEVEL

    if envs.VLLM_LOGGING_CONFIG_PATH:
        if not path.exists(envs.VLLM_LOGGING_CONFIG_PATH):
            raise RuntimeError(
                "Could not load logging config. File does not exist: %s",
                envs.VLLM_LOGGING_CONFIG_PATH,
            )
        with open(envs.VLLM_LOGGING_CONFIG_PATH, encoding="utf-8") as file:
            custom_config = json.loads(file.read())

        if not isinstance(custom_config, dict):
            raise ValueError(
                "Invalid logging config. Expected dict, got %s.",
                type(custom_config).__name__,
            )
        logging_config = custom_config

    for formatter in logging_config.get("formatters", {}).values():
        # This provides backwards compatibility after #10134.
        if formatter.get("class") == "vllm.logging.NewLineFormatter":
            formatter["class"] = "vllm.logging_utils.NewLineFormatter"

    if logging_config:
        dictConfig(logging_config)