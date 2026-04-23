def _default_for_input_result(result_schema: dict[str, Any], name: str | None) -> Any:
    """Return a type-appropriate sample value for an AgentInputBlock's result pin.

    Typed subclasses (AgentNumberInputBlock, AgentDateInputBlock, etc.)
    declare a specific type/format on their ``result`` output.  When dry-run
    has no user-supplied value, this generates a fallback that matches the
    expected type so downstream validation doesn't fail with a plain string.
    """
    pin_type = result_schema.get("type", "string")
    fmt = result_schema.get("format")

    if pin_type == "integer":
        return 0
    if pin_type == "number":
        return 0.0
    if pin_type == "boolean":
        return False
    if pin_type == "array":
        return []
    if pin_type == "object":
        return {}
    if fmt == "date":
        from datetime import date as _date  # noqa: PLC0415

        return _date.today().isoformat()
    if fmt == "time":
        return "00:00:00"
    # Default: use the block's name as a sample string.
    return name or "sample input"