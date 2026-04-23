async def build_flow(
    *,
    flow_id: uuid.UUID,
    background_tasks: LimitVertexBuildBackgroundTasks,
    inputs: Annotated[InputValueRequest | None, Body(embed=True)] = None,
    data: Annotated[FlowDataRequest | None, Body(embed=True)] = None,
    files: list[str] | None = None,
    stop_component_id: str | None = None,
    start_component_id: str | None = None,
    log_builds: bool = True,
    current_user: CurrentActiveUser,
    queue_service: Annotated[JobQueueService, Depends(get_queue_service)],
    flow_name: str | None = None,
    event_delivery: EventDeliveryType = EventDeliveryType.POLLING,
):
    """Build and process a flow, returning a job ID for event polling.

    This endpoint requires authentication through the CurrentActiveUser dependency.
    For public flows that don't require authentication, use the /build_public_tmp/flow_id/flow endpoint.

    Args:
        flow_id: UUID of the flow to build
        background_tasks: Background tasks manager
        inputs: Optional input values for the flow
        data: Optional flow data
        files: Optional files to include
        stop_component_id: Optional ID of component to stop at
        start_component_id: Optional ID of component to start from
        log_builds: Whether to log the build process
        current_user: The authenticated user
        queue_service: Queue service for job management
        flow_name: Optional name for the flow
        event_delivery: Optional event delivery type - default is streaming

    Returns:
        Dict with job_id that can be used to poll for build status
    """
    # Verify the flow exists and belongs to the requesting user (or is public).
    # Returns 404 for both "not found" and "not owned" to avoid UUID enumeration.
    # Note: intentionally extends _read_flow (flows.py) to also allow PUBLIC flows,
    # since build is a valid operation on shared flows.
    async with session_scope() as session:
        stmt = (
            select(Flow)
            .where(Flow.id == flow_id)
            .where((Flow.user_id == current_user.id) | (Flow.access_type == AccessTypeEnum.PUBLIC))
        )
        flow = (await session.exec(stmt)).first()
        if not flow:
            await logger.awarning(
                "Flow access denied for user %s: flow %s not found or not owned",
                current_user.id,
                flow_id,
            )
            raise HTTPException(status_code=404, detail=f"Flow with id {flow_id} not found")

    try:
        if data:
            validate_flow_for_current_settings(data.model_dump())
        elif flow and flow.data:
            validate_flow_for_current_settings(flow.data)
    except CustomComponentValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    job_id = await start_flow_build(
        flow_id=flow_id,
        background_tasks=background_tasks,
        inputs=inputs,
        data=data,
        files=files,
        stop_component_id=stop_component_id,
        start_component_id=start_component_id,
        log_builds=log_builds,
        current_user=current_user,
        queue_service=queue_service,
        flow_name=flow_name,
    )
    queue_service.register_job_owner(job_id, current_user.id)

    # This is required to support FE tests - we need to be able to set the event delivery to direct
    if event_delivery != EventDeliveryType.DIRECT:
        return {"job_id": job_id}
    return await get_flow_events_response(
        job_id=job_id,
        queue_service=queue_service,
        event_delivery=event_delivery,
    )