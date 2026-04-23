async def validate_flow(flow_id: str) -> dict[str, Any]:
    """Validate a flow and return structured per-component results.

    Streams the build inline (`event_delivery=direct`) and aggregates per-vertex
    results from `end_vertex` events. Fast-fails on the first failing component
    or top-level build error -- downstream vertices depend on upstream success
    and would not produce useful additional information.

    Args:
        flow_id: The flow UUID.
    """
    flow = await _get_flow(flow_id)
    expected = len(flow.get("data", {}).get("nodes", []))
    if expected == 0:
        return {"valid": True, "component_count": 0, "errors": [], "warnings": []}

    completed: set[str] = set()
    errors: list[dict[str, str]] = []

    try:
        async for event in _get_client().stream_post(f"/build/{flow_id}/flow?event_delivery=direct"):
            event_type = event.get("event", "")
            data = event.get("data") or {}

            if event_type == "end_vertex":
                build_data = data.get("build_data") or {}
                vertex_id = build_data.get("id") or ""
                if vertex_id:
                    completed.add(vertex_id)
                if not build_data.get("valid", False):
                    errors.append(
                        {
                            "component_id": vertex_id or "unknown",
                            "error": _extract_vertex_error(build_data),
                        }
                    )
                    # Fast-fail: downstream vertices won't run, no point waiting.
                    return {
                        "valid": False,
                        "component_count": len(completed),
                        "errors": errors,
                    }

            elif event_type == "error":
                # Top-level build failure (e.g. graph could not be constructed).
                message = data.get("exception") or data.get("reason") or data.get("error") or "Build error"
                return {
                    "valid": False,
                    "component_count": len(completed),
                    "errors": [{"component_id": "flow", "error": str(message)}],
                }

            elif event_type == "end":
                break
    except RuntimeError as exc:
        return {
            "valid": False,
            "error": f"Build request failed: {exc}",
            "component_count": len(completed),
            "errors": errors,
        }

    return {
        "valid": True,
        "component_count": len(completed),
        "errors": [],
    }