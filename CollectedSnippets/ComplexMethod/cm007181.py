async def emit_vertex_build_event(
    *,
    flow_id: str | UUID,
    vertex_id: str,
    valid: bool,
    params: Any,
    data_dict: dict | Any,
    artifacts_dict: dict | None = None,
    next_vertices_ids: list[str] | None = None,
    top_level_vertices: list[str] | None = None,
    inactivated_vertices: list[str] | None = None,
) -> None:
    """Emit end_vertex event for webhook real-time feedback.

    This is a helper function to emit SSE events when vertices are built.
    Errors are silently ignored as SSE emission is not critical.

    Args:
        flow_id: The flow ID
        vertex_id: The vertex ID that was built
        valid: Whether the build was successful
        params: Build parameters or error message
        data_dict: Build result data
        artifacts_dict: Build artifacts
        next_vertices_ids: IDs of vertices to run next (for UI animation)
        top_level_vertices: Top level vertices
        inactivated_vertices: Vertices that were inactivated
    """
    try:
        from datetime import datetime, timezone

        from langflow.services.event_manager import webhook_event_manager

        flow_id_str = str(flow_id)
        if not webhook_event_manager.has_listeners(flow_id_str):
            return

        duration = webhook_event_manager.get_build_duration(flow_id_str, vertex_id)

        # Convert Pydantic model to dict if necessary
        if hasattr(data_dict, "model_dump"):
            data_as_dict = data_dict.model_dump()
        elif isinstance(data_dict, dict):
            data_as_dict = data_dict
        else:
            data_as_dict = {}

        results = serialize_for_json(data_as_dict.get("results", {}))
        outputs = serialize_for_json(data_as_dict.get("outputs", {}))
        logs = serialize_for_json(data_as_dict.get("logs", {}))
        messages = serialize_for_json(data_as_dict.get("messages", []))

        vertex_data = {
            "results": results,
            "outputs": outputs,
            "logs": logs,
            "messages": messages,
            "duration": duration,
        }

        serialized_artifacts = serialize_for_json(artifacts_dict) if artifacts_dict else {}

        await webhook_event_manager.emit(
            flow_id_str,
            "end_vertex",
            {
                "build_data": {
                    "id": vertex_id,
                    "valid": valid,
                    "params": str(params) if params else None,
                    "data": vertex_data,
                    "artifacts": serialized_artifacts,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "messages": vertex_data.get("messages", []),
                    "inactivated_vertices": inactivated_vertices or [],
                    "next_vertices_ids": next_vertices_ids or [],
                    "top_level_vertices": top_level_vertices or [],
                }
            },
        )
    except ImportError:
        pass  # langflow not available (standalone lfx usage)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"SSE emission failed for vertex {vertex_id}: {exc}")