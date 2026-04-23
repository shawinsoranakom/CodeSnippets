def _extract_vertex_error(build_data: dict[str, Any]) -> str:
    """Best-effort error message from a failed end_vertex event payload.

    On failure, the build pipeline puts the exception in `params` and stuffs
    a structured error into the first output's `message`. Prefer the structured
    message; fall back to params; fall back to a generic string.
    """
    outputs = (build_data.get("data") or {}).get("outputs") or {}
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        message = output.get("message")
        if isinstance(message, dict) and message.get("errorMessage"):
            return str(message["errorMessage"])
    params = build_data.get("params")
    if params:
        return str(params)
    return "Unknown error"