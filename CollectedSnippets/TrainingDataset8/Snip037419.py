def _use_arrow() -> bool:
    """True if we're using Apache Arrow for DataFrame serialization."""
    # Explicitly coerce to bool here because mypy is (incorrectly) complaining
    # that we're trying to return 'Any'.
    return bool(config.get_option("global.dataFrameSerialization") == "arrow")