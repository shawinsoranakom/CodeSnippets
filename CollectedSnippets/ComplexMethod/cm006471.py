async def experimental_run_flow(
    *,
    session: DbSession,
    flow: Annotated[Flow, Depends(get_flow_by_id_or_endpoint_name)],
    inputs: list[InputValueRequest] | None = None,
    outputs: list[str] | None = None,
    tweaks: Annotated[Tweaks | None, Body(embed=True)] = None,
    stream: Annotated[bool, Body(embed=True)] = False,
    session_id: Annotated[None | str, Body(embed=True)] = None,
    api_key_user: Annotated[UserRead, Depends(api_key_security)],
) -> RunResponse:
    """Executes a specified flow by ID with optional input values, output selection, tweaks, and streaming capability.

    This endpoint supports running flows with caching to enhance performance and efficiency.

    ### Parameters:
    - `flow` (Flow): The flow object to be executed, resolved via dependency injection.
    - `inputs` (List[InputValueRequest], optional): A list of inputs specifying the input values and components
      for the flow. Each input can target specific components and provide custom values.
    - `outputs` (List[str], optional): A list of output names to retrieve from the executed flow.
      If not provided, all outputs are returned.
    - `tweaks` (Optional[Tweaks], optional): A dictionary of tweaks to customize the flow execution.
      The tweaks can be used to modify the flow's parameters and components.
      Tweaks can be overridden by the input values.
    - `stream` (bool, optional): Specifies whether the results should be streamed. Defaults to False.
    - `session_id` (Union[None, str], optional): An optional session ID to utilize existing session data for the flow
      execution.
    - `api_key_user` (User): The user associated with the current API key. Automatically resolved from the API key.

    ### Returns:
    A `RunResponse` object containing the selected outputs (or all if not specified) of the executed flow
    and the session ID.
    The structure of the response accommodates multiple inputs, providing a nested list of outputs for each input.

    ### Raises:
    HTTPException: Indicates issues with finding the specified flow, invalid input formats, or internal errors during
    flow execution.

    ### Example usage:
    ```json
    POST /run/flow_id
    x-api-key: YOUR_API_KEY
    Payload:
    {
        "inputs": [
            {"components": ["component1"], "input_value": "value1"},
            {"components": ["component3"], "input_value": "value2"}
        ],
        "outputs": ["Component Name", "component_id"],
        "tweaks": {"parameter_name": "value", "Component Name": {"parameter_name": "value"}, "component_id": {"parameter_name": "value"}}
        "stream": false
    }
    ```

    This endpoint facilitates complex flow executions with customized inputs, outputs, and configurations,
    catering to diverse application requirements.
    """  # noqa: E501
    # Get the flow from the id or name
    await check_flow_user_permission(flow=flow, api_key_user=api_key_user)

    session_service = get_session_service()
    flow_id_str = str(flow.id)
    if outputs is None:
        outputs = []
    if inputs is None:
        inputs = [InputValueRequest(components=[], input_value="")]

    if session_id:
        try:
            session_data = await session_service.load_session(session_id, flow_id=flow_id_str)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        graph, _artifacts = session_data or (None, None)
        if graph is None:
            msg = f"Session {session_id} not found"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    else:
        try:
            # Get the flow that matches the flow_id and belongs to the user
            # flow = session.query(Flow).filter(Flow.id == flow_id).filter(Flow.user_id == api_key_user.id).first()
            stmt = select(Flow).where(Flow.id == flow.id).where(Flow.user_id == api_key_user.id)
            flow = (await session.exec(stmt)).first()
        except sa.exc.StatementError as exc:
            # StatementError('(builtins.ValueError) badly formed hexadecimal UUID string')
            if "badly formed hexadecimal UUID string" in str(exc):
                await logger.aerror(f"Flow ID {flow_id_str} is not a valid UUID")
                # This means the Flow ID is not a valid UUID which means it can't find the flow
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        if flow is None:
            msg = f"Flow {flow_id_str} not found"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)

        if flow.data is None:
            msg = f"Flow {flow_id_str} has no data"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        try:
            graph_data = flow.data
            graph_data = process_tweaks(graph_data, tweaks or {})
            graph = Graph.from_payload(graph_data, flow_id=flow_id_str)
        except CustomComponentValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    try:
        task_result, session_id = await run_graph_internal(
            graph=graph,
            flow_id=flow_id_str,
            session_id=session_id,
            inputs=inputs,
            outputs=outputs,
            stream=stream,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return RunResponse(outputs=task_result, session_id=session_id)