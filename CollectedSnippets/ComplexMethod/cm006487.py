async def create_response(
    request: OpenAIResponsesRequest,
    background_tasks: BackgroundTasks,
    api_key_user: Annotated[UserRead, Depends(api_key_security)],
    telemetry_service: Annotated[TelemetryService, Depends(get_telemetry_service)],
    http_request: Request,
) -> OpenAIResponsesResponse | StreamingResponse | OpenAIErrorResponse:
    """Create a response using OpenAI Responses API format.

    This endpoint accepts a flow_id in the model parameter and processes
    the input through the specified Langflow flow.

    Args:
        request: OpenAI Responses API request with model (flow_id) and input
        background_tasks: FastAPI background task manager
        api_key_user: Authenticated user from API key
        http_request: The incoming HTTP request
        telemetry_service: Telemetry service for logging

    Returns:
        OpenAI-compatible response or streaming response

    Raises:
        HTTPException: For validation errors or flow execution issues
    """
    start_time = time.perf_counter()

    # Extract global variables from X-LANGFLOW-GLOBAL-VAR-* headers
    variables = extract_global_variables_from_headers(http_request.headers)

    await logger.adebug(f"All headers received: {list(http_request.headers.keys())}")
    await logger.adebug(f"Extracted global variables from headers: {list(variables.keys())}")

    # Validate tools parameter - error out if tools are provided
    if request.tools is not None:
        error_response = create_openai_error(
            message="Tools are not supported yet",
            type_="invalid_request_error",
            code="tools_not_supported",
        )
        return OpenAIErrorResponse(error=error_response["error"])

    # Get flow using the model field (which contains flow_id)
    try:
        flow = await get_flow_by_id_or_endpoint_name(request.model, str(api_key_user.id))
    except HTTPException:
        flow = None

    if flow is None:
        error_response = create_openai_error(
            message=f"Flow with id '{request.model}' not found",
            type_="invalid_request_error",
            code="flow_not_found",
        )
        return OpenAIErrorResponse(error=error_response["error"])

    try:
        # Process the request
        result = await run_flow_for_openai_responses(
            flow=flow,
            request=request,
            api_key_user=api_key_user,
            stream=request.stream,
            variables=variables,
        )

    except CustomComponentValidationError as exc:
        error_response = create_openai_error(
            message=str(exc),
            type_="invalid_request_error",
            code="custom_components_blocked",
        )
        return OpenAIErrorResponse(error=error_response["error"])

    except ValueError as exc:
        error_response = create_openai_error(
            message=str(exc),
            type_="invalid_request_error",
            code="invalid_flow_request",
        )
        return OpenAIErrorResponse(error=error_response["error"])

    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error processing OpenAI Responses request: {exc}")

        # Log telemetry for failed completion
        background_tasks.add_task(
            telemetry_service.log_package_run,
            RunPayload(
                run_is_webhook=False,
                run_seconds=int(time.perf_counter() - start_time),
                run_success=False,
                run_error_message=str(exc),
                run_id=None,  # OpenAI endpoint doesn't use simple_run_flow
            ),
        )

        # Return OpenAI-compatible error
        error_response = create_openai_error(
            message=str(exc),
            type_="processing_error",
        )
        return OpenAIErrorResponse(error=error_response["error"])

    # Log telemetry for successful completion
    if not request.stream:  # Only log for non-streaming responses
        end_time = time.perf_counter()
        background_tasks.add_task(
            telemetry_service.log_package_run,
            RunPayload(
                run_is_webhook=False,
                run_seconds=int(end_time - start_time),
                run_success=True,
                run_error_message="",
                run_id=None,  # OpenAI endpoint doesn't use simple_run_flow
            ),
        )

    return result