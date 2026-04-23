async def simple_run_flow_task(
    flow: Flow,
    input_request: SimplifiedAPIRequest,
    *,
    stream: bool = False,
    api_key_user: User | None = None,
    event_manager: EventManager | None = None,
    telemetry_service=None,
    start_time: float | None = None,
    run_id: str | None = None,
    emit_events: bool = False,
    flow_id: str | None = None,
):
    """Run a flow task as a BackgroundTask, therefore it should not throw exceptions.

    Args:
        flow: The flow to execute
        input_request: The simplified API request
        stream: Whether to stream results
        api_key_user: The user executing the flow
        event_manager: Event manager for streaming
        telemetry_service: Service for logging telemetry
        start_time: Start time for duration calculation
        run_id: Unique ID for this run
        emit_events: Whether to emit events to webhook_event_manager (for UI feedback)
        flow_id: Flow ID for event emission (required if emit_events=True)
    """
    should_emit = emit_events and flow_id

    # Create an EventManager that forwards events to webhook SSE if we should emit
    webhook_em = None
    if should_emit and event_manager is None and flow_id is not None:
        webhook_em = create_webhook_event_manager(flow_id, run_id)

    # Use provided event_manager or the webhook one
    effective_event_manager = event_manager or webhook_em

    try:
        if should_emit and flow_id is not None:
            vertex_ids = _get_vertex_ids_from_flow(flow)
            await webhook_event_manager.emit(
                flow_id,
                "vertices_sorted",
                {"ids": vertex_ids, "to_run": vertex_ids, "run_id": run_id},
            )

        result = await simple_run_flow(
            flow=flow,
            input_request=input_request,
            stream=stream,
            api_key_user=api_key_user,
            event_manager=effective_event_manager,
            run_id=run_id,
        )

        if should_emit and flow_id is not None:
            await webhook_event_manager.emit(flow_id, "end", {"run_id": run_id, "success": True})

        if telemetry_service and start_time is not None:
            await telemetry_service.log_package_run(
                RunPayload(
                    run_is_webhook=True,
                    run_seconds=int(time.perf_counter() - start_time),
                    run_success=True,
                    run_error_message="",
                    run_id=run_id,
                )
            )
        return result  # noqa: TRY300

    except Exception as exc:  # noqa: BLE001
        await logger.aexception(f"Error running flow {flow.id} task")

        if should_emit and flow_id is not None:
            await webhook_event_manager.emit(flow_id, "end", {"run_id": run_id, "success": False, "error": str(exc)})

        if telemetry_service and start_time is not None:
            await telemetry_service.log_package_run(
                RunPayload(
                    run_is_webhook=True,
                    run_seconds=int(time.perf_counter() - start_time),
                    run_success=False,
                    run_error_message=str(exc),
                    run_id=run_id,
                )
            )
        return None