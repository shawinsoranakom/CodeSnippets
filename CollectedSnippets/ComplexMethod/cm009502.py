def _get_langsmith_inheritable_metadata_from_config(
    config: RunnableConfig,
) -> dict[str, Any] | None:
    """Get LangSmith-only inheritable metadata defaults derived from config."""
    configurable = config.get("configurable") or {}
    metadata = {
        key: value
        for key, value in configurable.items()
        if not key.startswith("__")
        and isinstance(value, (str, int, float, bool))
        and key not in config.get("metadata", {})
        and key not in CONFIGURABLE_TO_TRACING_METADATA_EXCLUDED_KEYS
    }
    return metadata or None