async def build_custom_component(params: dict, custom_component: CustomComponent):
    if "retriever" in params and hasattr(params["retriever"], "as_retriever"):
        params["retriever"] = params["retriever"].as_retriever()

    # Determine if the build method is asynchronous
    is_async = inspect.iscoroutinefunction(custom_component.build)

    # New feature: the component has a list of outputs and we have
    # to check the vertex.edges to see which is connected (coulb be multiple)
    # and then we'll get the output which has the name of the method we should call.
    # the methods don't require any params because they are already set in the custom_component
    # so we can just call them

    if is_async:
        # Await the build method directly if it's async
        build_result = await custom_component.build(**params)
    else:
        # Call the build method directly if it's sync
        build_result = custom_component.build(**params)
    custom_repr = custom_component.custom_repr()
    if custom_repr is None and isinstance(build_result, dict | Data | str):
        custom_repr = build_result
    if not isinstance(custom_repr, str):
        custom_repr = str(custom_repr)
    raw = custom_component.repr_value
    if hasattr(raw, "data") and raw is not None:
        raw = raw.data

    elif hasattr(raw, "model_dump") and raw is not None:
        raw = raw.model_dump()
    if raw is None and isinstance(build_result, dict | Data | str):
        raw = build_result.data if isinstance(build_result, Data) else build_result

    artifact_type = get_artifact_type(custom_component.repr_value or raw, build_result)
    raw = post_process_raw(raw, artifact_type)
    artifact = {"repr": custom_repr, "raw": raw, "type": artifact_type}

    vertex = custom_component.get_vertex()
    if vertex is not None:
        custom_component.set_artifacts({vertex.outputs[0].get("name"): artifact})
        custom_component.set_results({vertex.outputs[0].get("name"): build_result})
        return custom_component, build_result, artifact

    msg = "Custom component does not have a vertex"
    raise ValueError(msg)