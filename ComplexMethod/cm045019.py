def _build_namespace(context: Any) -> dict[str, Any]:
    """Build the variable namespace from a StepContext."""
    ns: dict[str, Any] = {}
    if hasattr(context, "inputs"):
        ns["inputs"] = context.inputs or {}
    if hasattr(context, "steps"):
        ns["steps"] = context.steps or {}
    if hasattr(context, "item"):
        ns["item"] = context.item
    if hasattr(context, "fan_in"):
        ns["fan_in"] = context.fan_in or {}
    return ns