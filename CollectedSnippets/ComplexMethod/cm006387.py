async def execute_flow_file(
    flow_filename: str,
    input_value: str | None = None,
    global_variables: dict[str, str] | None = None,
    *,
    verbose: bool = False,  # noqa: ARG001
    user_id: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    api_key_var: str | None = None,
) -> dict:
    """Execute a flow from a Python or JSON file.

    Supports both .py and .json flows. When both exist, .py takes priority.

    Args:
        flow_filename: Name of the flow file (e.g., "MyFlow.json" or "my_flow.py")
        input_value: Input value to pass to the flow
        global_variables: Dict of global variables to inject into the flow context
        verbose: Kept for backward compatibility (currently unused)
        user_id: User ID for components that require user context
        session_id: Unique session ID to isolate memory between requests
        provider: Model provider to inject into Agent nodes
        model_name: Model name to inject into Agent nodes
        api_key_var: API key variable name to inject into Agent nodes

    Returns:
        dict: Result from flow execution

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

        if user_id:
            graph.user_id = user_id
        if session_id:
            graph.session_id = session_id

        if global_variables:
            if "request_variables" not in graph.context:
                graph.context["request_variables"] = {}
            graph.context["request_variables"].update(global_variables)

        flow_id = (global_variables or {}).get("FLOW_ID")
        if flow_id:
            graph.flow_id = flow_id
        graph.flow_name = graph.flow_name or flow_filename

        graph.prepare()
        inputs = InputValueRequest(input_value=input_value) if input_value else None

        results = [result async for result in graph.async_start(inputs=inputs)]
        return extract_structured_result(results)

    except HTTPException:
        raise
    except CustomComponentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        logger.error(f"Flow execution error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while executing the flow.") from e
    except Exception as e:
        logger.error(f"Flow execution error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while executing the flow.") from e