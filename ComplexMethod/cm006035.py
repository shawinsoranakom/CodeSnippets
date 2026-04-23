async def run_via_arun(
    graph: Graph,
    inputs: list[InputValueRequest] | None = None,
    outputs: list[str] | None = None,
) -> ExecutionTrace:
    """Run graph using arun path and capture trace.

    This mimics how the /api/v1/run endpoint executes graphs.
    """
    trace = ExecutionTrace(path_name="arun")
    tracer = ExecutionTracer(graph, trace)

    try:
        tracer.install()
        graph.prepare()

        # Convert inputs to the format expected by arun
        inputs_list = []
        inputs_components = []
        types = []

        if inputs:
            for input_request in inputs:
                inputs_list.append({"message": input_request.input_value})
                inputs_components.append(input_request.components or [])
                types.append(input_request.type or "chat")

        results = await graph.arun(
            inputs=inputs_list,
            inputs_components=inputs_components,
            types=types,
            outputs=outputs or [],
            session_id=graph.session_id or "test-session",
        )

        trace.final_outputs = results

    except Exception as e:
        trace.error = e
    finally:
        tracer.uninstall()

    return trace