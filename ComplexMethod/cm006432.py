async def build_public_tmp(
    *,
    background_tasks: LimitVertexBuildBackgroundTasks,
    flow_id: uuid.UUID,
    inputs: Annotated[InputValueRequest | None, Body(embed=True)] = None,
    files: list[str] | None = None,
    stop_component_id: str | None = None,
    start_component_id: str | None = None,
    log_builds: bool | None = True,
    flow_name: str | None = None,
    request: Request,
    queue_service: Annotated[JobQueueService, Depends(get_queue_service)],
    authenticated_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    event_delivery: EventDeliveryType = EventDeliveryType.POLLING,
):
    """Build a public flow without requiring authentication.

    This endpoint is specifically for public flows that don't require authentication.
    It uses a client_id cookie to create a deterministic flow ID for tracking purposes.

    Security Note:
    - The 'data' parameter is NOT accepted to prevent flow definition tampering
    - Public flows must execute the stored flow definition only
    - The flow definition is always loaded from the database

    The endpoint:
    1. Verifies the requested flow is marked as public in the database
    2. Creates a deterministic UUID based on client_id and flow_id
    3. Uses the flow owner's permissions to build the flow
    4. Always loads the flow definition from the database

    Requirements:
    - The flow must be marked as PUBLIC in the database
    - The request must include a client_id cookie

    Args:
        flow_id: UUID of the public flow to build
        background_tasks: Background tasks manager
        inputs: Optional input values for the flow
        files: Optional files to include
        stop_component_id: Optional ID of component to stop at
        start_component_id: Optional ID of component to start from
        log_builds: Whether to log the build process
        flow_name: Optional name for the flow
        request: FastAPI request object (needed for cookie access)
        queue_service: Queue service for job management
        authenticated_user: Optional authenticated user (resolved from cookie/token if present)
        event_delivery: Optional event delivery type - default is streaming

    Returns:
        Dict with job_id that can be used to poll for build status
    """
    try:
        # Verify this is a public flow and get the associated user
        client_id = request.cookies.get("client_id")
        # Only use authenticated user_id when auto-login is disabled.
        # When AUTO_LOGIN=TRUE, the frontend uses client_id for UUID v5,
        # so the backend must match to avoid flow_id mismatch.
        auth_settings = get_settings_service().auth_settings
        authenticated_user_id = authenticated_user.id if authenticated_user and not auth_settings.AUTO_LOGIN else None
        owner_user, new_flow_id = await verify_public_flow_and_get_user(
            flow_id=flow_id,
            client_id=client_id,
            authenticated_user_id=authenticated_user_id,
        )

        # Validate the stored flow data after the public-access boundary.
        # Public flows never accept client-supplied data.
        async with session_scope() as session:
            flow = await session.get(Flow, flow_id)
            if flow and flow.data:
                validate_flow_for_current_settings(flow.data)

        # flow_id=new_flow_id for tracking/sessions/messages (virtual, per-user isolation).
        # source_flow_id=flow_id to load the actual flow data from the database.
        job_id = await start_flow_build(
            flow_id=new_flow_id,
            source_flow_id=flow_id,
            background_tasks=background_tasks,
            inputs=inputs,
            data=None,  # Always None - public flows load from database only
            files=files,
            stop_component_id=stop_component_id,
            start_component_id=start_component_id,
            log_builds=log_builds or False,
            current_user=owner_user,
            queue_service=queue_service,
            flow_name=flow_name or f"{authenticated_user_id or client_id}_{flow_id}",
        )
    except CustomComponentValidationError as exc:
        await logger.awarning(f"Public flow validation failed: {exc}")
        raise HTTPException(status_code=400, detail="This flow cannot be executed.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await logger.aexception("Error building public flow")
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if event_delivery != EventDeliveryType.DIRECT:
        return {"job_id": job_id}
    return await get_flow_events_response(
        job_id=job_id,
        queue_service=queue_service,
        event_delivery=event_delivery,
    )