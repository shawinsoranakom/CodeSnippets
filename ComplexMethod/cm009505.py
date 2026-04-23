def patch_config(
    config: RunnableConfig | None,
    *,
    callbacks: BaseCallbackManager | None = None,
    recursion_limit: int | None = None,
    max_concurrency: int | None = None,
    run_name: str | None = None,
    configurable: dict[str, Any] | None = None,
) -> RunnableConfig:
    """Patch a config with new values.

    Args:
        config: The config to patch.
        callbacks: The callbacks to set.
        recursion_limit: The recursion limit to set.
        max_concurrency: The max concurrency to set.
        run_name: The run name to set.
        configurable: The configurable to set.

    Returns:
        The patched config.
    """
    config = ensure_config(config)
    if callbacks is not None:
        # If we're replacing callbacks, we need to unset run_name
        # As that should apply only to the same run as the original callbacks
        config["callbacks"] = callbacks
        if "run_name" in config:
            del config["run_name"]
        if "run_id" in config:
            del config["run_id"]
    if recursion_limit is not None:
        config["recursion_limit"] = recursion_limit
    if max_concurrency is not None:
        config["max_concurrency"] = max_concurrency
    if run_name is not None:
        config["run_name"] = run_name
    if configurable is not None:
        config["configurable"] = {**config.get("configurable", {}), **configurable}
    return config