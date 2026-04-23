async def execute_sync_workflow(
    workflow_request: WorkflowExecutionRequest,
    flow: FlowRead,
    job_id: UUID,
    api_key_user: UserRead,
    background_tasks: BackgroundTasks,  # noqa: ARG001
    http_request: Request,
) -> WorkflowExecutionResponse:
    """Execute workflow synchronously and return complete results.

    This function implements a two-tier error handling strategy:
        1. System-level errors (validation, graph build): Raised as exceptions
        2. Component execution errors: Returned in response body with HTTP 200

    This approach allows clients to receive partial results even when some
    components fail, which is useful for debugging and incremental processing.

    Execution Flow:
        1. Parse flat inputs into tweaks and session_id
        2. Validate flow data exists
        3. Extract context from HTTP headers
        4. Build graph from flow data with tweaks applied
        5. Identify terminal nodes for execution
        6. Execute graph and collect results
        7. Convert V1 RunResponse to V2 WorkflowExecutionResponse

    Args:
        workflow_request: The workflow execution request with inputs and configuration
        flow: The flow model from database
        job_id: Generated job ID for tracking this execution
        api_key_user: Authenticated user for permission checks
        background_tasks: FastAPI background tasks (unused in sync mode)
        http_request: The HTTP request object for extracting headers

    Returns:
        WorkflowExecutionResponse: Complete execution results with outputs and metadata

    Raises:
        WorkflowValidationError: If flow data is None or graph build fails
    """
    # Parse flat inputs structure
    tweaks, session_id = parse_flat_inputs(workflow_request.inputs or {})

    # Validate flow data - this is a system error, not execution error
    if flow.data is None:
        msg = f"Flow {flow.id} has no data. The flow may be corrupted."
        raise WorkflowValidationError(msg)

    # Extract request-level variables from headers (similar to V1)
    # Headers with prefix X-LANGFLOW-GLOBAL-VAR-* are extracted and made available to components
    request_variables = extract_global_variables_from_headers(http_request.headers)

    # Build context from request variables (similar to V1's _run_flow_internal)
    context = {"request_variables": request_variables} if request_variables else None

    # Build graph - system error if this fails
    try:
        flow_id_str = str(flow.id)
        user_id = str(api_key_user.id)
        # Use deepcopy to prevent mutation of the original flow.data
        # process_tweaks modifies nested dictionaries in-place
        graph_data = deepcopy(flow.data)
        graph_data = process_tweaks(graph_data, tweaks, stream=False)
        # Pass context to graph (similar to V1's simple_run_flow)
        # This allows components to access request metadata via graph.context
        graph = Graph.from_payload(
            graph_data, flow_id=flow_id_str, user_id=user_id, flow_name=flow.name, context=context
        )
        # Set run_id for tracing/logging (similar to V1's simple_run_flow)
        graph.set_run_id(job_id)
    except Exception as e:
        msg = f"Failed to build graph from flow data: {e!s}"
        raise WorkflowValidationError(msg) from e

    # Get terminal nodes - these are the outputs we want
    terminal_node_ids = graph.get_terminal_nodes()

    # Execute graph - component errors are caught and returned in response body
    job_service = get_job_service()
    await job_service.create_job(job_id=job_id, flow_id=flow_id_str, user_id=api_key_user.id)
    try:
        task_result, execution_session_id = await job_service.execute_with_status(
            job_id=job_id,
            run_coro_func=run_graph_internal,
            graph=graph,
            flow_id=flow_id_str,
            session_id=session_id,
            inputs=None,
            outputs=terminal_node_ids,
            stream=False,
        )

        # Build RunResponse
        run_response = RunResponse(outputs=task_result, session_id=execution_session_id)
        # Convert to WorkflowExecutionResponse
        return run_response_to_workflow_response(
            run_response=run_response,
            flow_id=workflow_request.flow_id,
            job_id=str(job_id),
            workflow_request=workflow_request,
            graph=graph,
        )

    except asyncio.CancelledError:
        # Re-raise CancelledError to allow timeout mechanism to work properly
        # This ensures asyncio.wait_for() can properly cancel and raise TimeoutError
        raise
    except asyncio.TimeoutError as e:
        # Re-raise TimeoutError to allow timeout mechanism to work properly
        # This ensures asyncio.wait_for() can properly cancel and raise TimeoutError
        raise WorkflowTimeoutError from e
    except Exception as exc:  # noqa: BLE001
        # Component execution errors - return in response body with HTTP 200
        # This allows partial results and detailed error information per component
        return create_error_response(
            flow_id=workflow_request.flow_id,
            job_id=job_id,
            workflow_request=workflow_request,
            error=exc,
        )