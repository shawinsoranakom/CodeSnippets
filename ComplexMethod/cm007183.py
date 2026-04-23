async def log_vertex_build(
    *,
    flow_id: str | UUID,
    vertex_id: str,
    valid: bool,
    params: Any,
    data: dict | Any,
    artifacts: dict | None = None,
    job_id: str | None = None,
) -> None:
    """Asynchronously logs a vertex build record if vertex build storage is enabled.

    This is a lightweight implementation that only logs if database service is available.
    When running within langflow, it will use langflow's database service to persist the build.
    When running standalone (lfx only), it will only log debug messages.
    """
    try:
        # Try to use langflow's services if available (when running within langflow)
        try:
            from langflow.services.deps import get_db_service as langflow_get_db_service
            from langflow.services.deps import get_settings_service as langflow_get_settings_service

            settings_service = langflow_get_settings_service()
            if not settings_service:
                return
            if not getattr(settings_service.settings, "vertex_builds_storage_enabled", False):
                return

            if isinstance(flow_id, str):
                flow_id = UUID(flow_id)

            from langflow.services.database.models.vertex_builds.crud import (
                log_vertex_build as crud_log_vertex_build,
            )
            from langflow.services.database.models.vertex_builds.model import VertexBuildBase

            # Convert data to dict if it's a pydantic model
            data_dict = data
            if hasattr(data, "model_dump"):
                data_dict = data.model_dump()
            elif hasattr(data, "dict"):
                data_dict = data.dict()

            # Convert artifacts to dict if it's a pydantic model
            artifacts_dict = artifacts
            if artifacts is not None:
                if hasattr(artifacts, "model_dump"):
                    artifacts_dict = artifacts.model_dump()
                elif hasattr(artifacts, "dict"):
                    artifacts_dict = artifacts.dict()

            vertex_build = VertexBuildBase(
                flow_id=flow_id,
                id=vertex_id,
                valid=valid,
                params=str(params) if params else None,
                data=data_dict,
                artifacts=artifacts_dict,
                job_id=job_id,
            )

            db_service = langflow_get_db_service()
            if db_service is None:
                return

            async with db_service._with_session() as session:  # noqa: SLF001
                await crud_log_vertex_build(session, vertex_build)

            # Note: emit_vertex_build_event is NOT called here because it needs
            # next_vertices_ids which are only available after graph.get_next_runnable_vertices()
            # The event is emitted separately in graph._execute_tasks() with complete data.

        except ImportError:
            # Fallback for standalone lfx usage (without langflow)
            settings_service = get_settings_service()
            if not settings_service or not getattr(settings_service.settings, "vertex_builds_storage_enabled", False):
                return

            if isinstance(flow_id, str):
                flow_id = UUID(flow_id)

            # Log basic vertex build info - concrete implementation is in langflow
            logger.debug(f"Vertex build logged: vertex={vertex_id}, flow={flow_id}, valid={valid}")

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Error logging vertex build: {exc}")