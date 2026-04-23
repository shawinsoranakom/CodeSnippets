def _cleanup_llm_representation(serialized: Any, depth: int) -> None:
    """Remove non-serializable objects from a serialized object."""
    if depth > _MAX_CLEANUP_DEPTH:  # Don't cooperate for pathological cases
        return

    if not isinstance(serialized, dict):
        return

    if (
        "type" in serialized
        and serialized["type"] == "not_implemented"
        and "repr" in serialized
    ):
        del serialized["repr"]

    if "graph" in serialized:
        del serialized["graph"]

    if "kwargs" in serialized:
        kwargs = serialized["kwargs"]

        for value in kwargs.values():
            _cleanup_llm_representation(value, depth + 1)