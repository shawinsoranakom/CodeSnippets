async def run_flow(
    inputs: dict | list[dict] | None = None,
    tweaks: dict | None = None,  # noqa: ARG001
    flow_id: str | None = None,  # noqa: ARG001
    flow_name: str | None = None,  # noqa: ARG001
    output_type: str | None = "chat",
    user_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    graph: Graph | None = None,
) -> list[RunOutputs]:
    """Run a flow with given inputs.

    Args:
        inputs: Input values for the flow.
        tweaks: Optional tweaks to apply.
        flow_id: The flow ID to run.
        flow_name: The flow name to run.
        output_type: The type of output to return.
        user_id: The user ID.
        run_id: Optional run ID.
        session_id: Optional session ID.
        graph: Optional pre-loaded graph.

    Returns:
        List of run outputs.
    """
    if user_id is None:
        msg = "Session is invalid"
        raise ValueError(msg)

    if graph is None:
        # In lfx, we can't load flows from database
        msg = "run_flow requires a graph parameter in lfx"
        raise ValueError(msg)

    if run_id:
        graph.set_run_id(UUID(run_id))
    if session_id:
        graph.session_id = session_id
    if user_id:
        graph.user_id = user_id

    if inputs is None:
        inputs = []
    if isinstance(inputs, dict):
        inputs = [inputs]

    inputs_list = []
    inputs_components = []
    types = []

    for input_dict in inputs:
        inputs_list.append({INPUT_FIELD_NAME: input_dict.get("input_value", "")})
        inputs_components.append(input_dict.get("components", []))
        types.append(input_dict.get("type", "chat"))

    outputs = [
        vertex.id
        for vertex in graph.vertices
        if output_type == "debug"
        or (vertex.is_output and (output_type == "any" or (output_type and output_type in str(vertex.id).lower())))
    ]

    # In lfx, we don't have settings service, so use False as default
    fallback_to_env_vars = False

    return await graph.arun(
        inputs_list,
        outputs=outputs,
        inputs_components=inputs_components,
        types=types,
        fallback_to_env_vars=fallback_to_env_vars,
    )