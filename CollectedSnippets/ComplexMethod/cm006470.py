async def _run_flow_internal(
    *,
    background_tasks: BackgroundTasks,
    flow: FlowRead | None,
    input_request: SimplifiedAPIRequest | None,
    stream: bool,
    api_key_user: User | UserRead,
    context: dict | None,
    http_request: Request,
) -> StreamingResponse | RunResponse:
    """Internal function containing the core business logic for running a flow.

    This function is shared between session-based and API key-based authentication endpoints.

    Args:
        background_tasks (BackgroundTasks): FastAPI background task manager
        flow (FlowRead | None): The flow to execute, loaded via dependency
        input_request (SimplifiedAPIRequest | None): Input parameters for the flow
        stream (bool): Whether to stream the response
        api_key_user (User | UserRead): Authenticated user (either from session or API key)
        context (dict | None): Optional context to pass to the flow
        http_request (Request): The incoming HTTP request for extracting global variables

    Returns:
        Union[StreamingResponse, RunResponse]: Either a streaming response for real-time results
        or a RunResponse with the complete execution results

    Raises:
        HTTPException: For flow not found (404) or invalid input (400)
        APIException: For internal execution errors (500)
    """
    await check_flow_user_permission(flow=flow, api_key_user=api_key_user)

    telemetry_service = get_telemetry_service()

    # If input_request is None, manually parse the request body
    # This happens when FastAPI can't automatically parse it due to the Request parameter
    if input_request is None:
        input_request = await parse_input_request_from_body(http_request)

    if flow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")

    # Extract request-level variables from headers with prefix X-LANGFLOW-GLOBAL-VAR-*
    request_variables = extract_global_variables_from_headers(http_request.headers)

    # Merge request variables with existing context
    if request_variables:
        if context is None:
            context = {"request_variables": request_variables}
        else:
            context = context.copy()  # Don't modify the original context
            context["request_variables"] = request_variables

    start_time = time.perf_counter()

    if stream:
        asyncio_queue: asyncio.Queue = asyncio.Queue()
        asyncio_queue_client_consumed: asyncio.Queue = asyncio.Queue()
        event_manager = create_stream_tokens_event_manager(queue=asyncio_queue)
        main_task = asyncio.create_task(
            run_flow_generator(
                flow=flow,
                input_request=input_request,
                api_key_user=api_key_user,
                event_manager=event_manager,
                client_consumed_queue=asyncio_queue_client_consumed,
                context=context,
            )
        )

        async def on_disconnect() -> None:
            await logger.adebug("Client disconnected, closing tasks")
            main_task.cancel()

        return StreamingResponse(
            consume_and_yield(asyncio_queue, asyncio_queue_client_consumed),
            background=on_disconnect,
            media_type="text/event-stream",
        )

    run_id = str(uuid4())
    try:
        result = await simple_run_flow(
            flow=flow,
            input_request=input_request,
            stream=stream,
            api_key_user=api_key_user,
            context=context,
            run_id=run_id,
        )
        end_time = time.perf_counter()
        background_tasks.add_task(
            telemetry_service.log_package_run,
            RunPayload(
                run_is_webhook=False,
                run_seconds=int(end_time - start_time),
                run_success=True,
                run_error_message="",
                run_id=run_id,
            ),
        )

    except ValueError as exc:
        background_tasks.add_task(
            telemetry_service.log_package_run,
            RunPayload(
                run_is_webhook=False,
                run_seconds=int(time.perf_counter() - start_time),
                run_success=False,
                run_error_message=str(exc),
                run_id=run_id,
            ),
        )
        if "badly formed hexadecimal UUID string" in str(exc):
            # This means the Flow ID is not a valid UUID which means it can't find the flow
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if isinstance(exc, CustomComponentValidationError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if "not found" in str(exc):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=exc, flow=flow) from exc
    except InvalidChatInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        background_tasks.add_task(
            telemetry_service.log_package_run,
            RunPayload(
                run_is_webhook=False,
                run_seconds=int(time.perf_counter() - start_time),
                run_success=False,
                run_error_message=str(exc),
                run_id=run_id,
            ),
        )
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=exc, flow=flow) from exc

    return result