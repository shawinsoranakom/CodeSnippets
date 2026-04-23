async def run_flow(
    inputs: dict | list[dict] | None = None,
    tweaks: dict | None = None,
    flow_id: str | None = None,
    flow_name: str | None = None,
    output_type: str | None = "chat",
    user_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    graph: Graph | None = None,
) -> list[RunOutputs]:
    if user_id is None:
        msg = "Session is invalid"
        raise ValueError(msg)
    if graph is None:
        graph = await load_flow(user_id, flow_id, flow_name, tweaks)
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
        inputs_list.append({INPUT_FIELD_NAME: cast("str", input_dict.get("input_value"))})
        inputs_components.append(input_dict.get("components", []))
        types.append(input_dict.get("type", "chat"))

    outputs = [
        vertex.id
        for vertex in graph.vertices
        if output_type == "debug"
        or (
            vertex.is_output and (output_type == "any" or output_type in vertex.id.lower())  # type: ignore[operator]
        )
    ]

    fallback_to_env_vars = get_settings_service().settings.fallback_to_env_var

    return await graph.arun(
        inputs_list,
        outputs=outputs,
        inputs_components=inputs_components,
        types=types,
        fallback_to_env_vars=fallback_to_env_vars,
    )