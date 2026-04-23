def ensure_config(config: RunnableConfig | None = None) -> RunnableConfig:
    """Ensure that a config is a dict with all keys present.

    Args:
        config: The config to ensure.

    Returns:
        The ensured config.
    """
    empty = RunnableConfig(
        tags=[],
        metadata={},
        callbacks=None,
        recursion_limit=DEFAULT_RECURSION_LIMIT,
        configurable={},
    )
    if var_config := var_child_runnable_config.get():
        empty.update(
            cast(
                "RunnableConfig",
                {
                    k: v.copy() if k in COPIABLE_KEYS else v  # type: ignore[attr-defined]
                    for k, v in var_config.items()
                    if v is not None
                },
            )
        )
    if config is not None:
        empty.update(
            cast(
                "RunnableConfig",
                {
                    k: v.copy() if k in COPIABLE_KEYS else v  # type: ignore[attr-defined]
                    for k, v in config.items()
                    if v is not None and k in CONFIG_KEYS
                },
            )
        )
    if config is not None:
        for k, v in config.items():
            if k not in CONFIG_KEYS and v is not None:
                empty["configurable"][k] = v
    for configurable_key in ("model", "checkpoint_ns"):
        if (
            isinstance(
                configurable_value := empty.get("configurable", {}).get(
                    configurable_key
                ),
                str,
            )
            and configurable_key not in empty["metadata"]
        ):
            empty["metadata"][configurable_key] = configurable_value
    return empty