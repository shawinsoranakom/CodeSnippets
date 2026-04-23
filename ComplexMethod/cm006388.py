async def execute_flow_file_streaming(
    flow_filename: str,
    input_value: str | None = None,
    global_variables: dict[str, str] | None = None,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    api_key_var: str | None = None,
    is_disconnected: Callable[[], Coroutine[Any, Any, bool]] | None = None,
    cancel_event: asyncio.Event | None = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """Execute a flow from a Python or JSON file with token streaming.

    Supports both .py and .json flows. When both exist, .py takes priority.

    Yields events as they occur:
    - ("token", chunk): Token chunk from LLM streaming
    - ("end", result): Final result when flow completes
    - ("cancelled", {}): Flow was cancelled

    Args:
        flow_filename: Name of the flow file (e.g., "MyFlow.json" or "my_flow.py")
        input_value: Input value to pass to the flow
        global_variables: Dict of global variables to inject into the flow context
        user_id: User ID for components that require user context
        session_id: Unique session ID to isolate memory between requests
        provider: Model provider to inject into Agent nodes
        model_name: Model name to inject into Agent nodes
        api_key_var: API key variable name to inject into Agent nodes
        is_disconnected: Async function to check if client disconnected
        cancel_event: Event to signal cancellation from outside

    Yields:
        tuple[str, Any]: Event type and data pairs

    Raises:
        HTTPException: If flow file not found or execution fails
    """
    flow_path, flow_type = resolve_flow_path(flow_filename)

    try:
        graph = await load_graph_for_execution(
            flow_path,
            flow_type,
            provider,
            model_name,
            api_key_var,
            provider_vars=global_variables,
        )
    except CustomComponentValidationError as e:
        logger.error(f"Flow preparation error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (json.JSONDecodeError, OSError, ValueError) as e:
        logger.error(f"Flow preparation error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while preparing the flow.") from e

    event_queue: asyncio.Queue[tuple[str, bytes, float] | None] = asyncio.Queue(maxsize=STREAMING_QUEUE_MAX_SIZE)
    event_manager = create_default_event_manager(event_queue)
    execution_result = FlowExecutionResult()

    flow_task = asyncio.create_task(
        _run_graph_with_events(
            graph=graph,
            input_value=input_value,
            global_variables=global_variables,
            user_id=user_id,
            session_id=session_id,
            event_manager=event_manager,
            event_queue=event_queue,
            execution_result=execution_result,
        )
    )

    cancelled = False
    try:
        async for event_type, chunk in consume_streaming_events(event_queue, is_disconnected, cancel_event):
            if event_type == "token":
                yield ("token", chunk)
            elif event_type == "end":
                break
            elif event_type == "cancelled":
                cancelled = True
                break
    except GeneratorExit:
        logger.info("Generator closed externally, cancelling flow")
        cancelled = True
    finally:
        if not flow_task.done():
            flow_task.cancel()
            try:
                await flow_task
            except asyncio.CancelledError:
                logger.info("Flow task cancelled")

    if cancelled:
        yield ("cancelled", {})
        return

    if execution_result.has_error:
        logger.error(f"Flow execution error: {execution_result.error}")
        # Raise a FlowExecutionError that keeps the raw error internal:
        # the public `detail` stays generic so no stack traces leak to HTTP clients,
        # while internal callers read `original_error_message` to build friendly UX.
        raise FlowExecutionError(
            original_error_message=str(execution_result.error),
        ) from execution_result.error

    yield ("end", execution_result.result if execution_result.has_result else {})