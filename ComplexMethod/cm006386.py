async def _run_graph_with_events(
    graph: "Graph",
    input_value: str | None,
    global_variables: dict[str, str] | None,
    user_id: str | None,
    session_id: str | None,
    event_manager: EventManager,
    event_queue: asyncio.Queue,
    execution_result: FlowExecutionResult,
) -> None:
    """Execute graph and store result, signaling completion via queue."""
    try:
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
        graph.flow_name = graph.flow_name or "Assistant Flow"

        graph.prepare()
        inputs = InputValueRequest(input_value=input_value) if input_value else None

        results = [result async for result in graph.async_start(inputs=inputs, event_manager=event_manager)]
        execution_result.result = extract_structured_result(results)
    except Exception as e:  # noqa: BLE001
        execution_result.error = e
        logger.error(f"Flow execution error: {e}")
    finally:
        await event_queue.put(None)