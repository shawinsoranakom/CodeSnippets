def create_wxo_flow_tool(
    *,
    flow_payload: BaseFlowArtifact[WatsonxFlowArtifactProviderData],
    connections: dict[str, str],
) -> tuple[dict[str, Any], bytes]:
    """Create a Watsonx Orchestrate flow tool specification.

    Given a flow payload and connections dictionary,
    create a Watsonx Orchestrate flow tool specification
    and the supporting artifacts of the requirements.txt
    and the flow json file.

    Args:
        flow_payload: The flow payload to create the tool specification for.
        connections: The connections dictionary to create the tool specification for.

    Returns:
        Tuple[dict[str, Any], bytes]: a tuple containing:
            - tool_payload: The Watsonx Orchestrate flow tool specification.
            - artifacts: The supporting artifacts (the requirements.txt
                and the flow json file) for the tool.
    """
    # provider_data might break tool runtime expectations with unexpected top-level keys
    flow_definition = flow_payload.model_dump(exclude={"provider_data"})
    logger.debug(
        "create_wxo_flow_tool: flow name='%s', id='%s', connections=%s",
        flow_definition.get("name"),
        flow_definition.get("id"),
        connections,
    )

    flow_provider_data = flow_payload.provider_data
    if not isinstance(flow_provider_data, WatsonxFlowArtifactProviderData):
        msg = "Flow payload provider_data must be a WatsonxFlowArtifactProviderData model instance."
        raise InvalidContentError(message=msg)
    project_id = str(flow_provider_data.project_id).strip()

    flow_definition.update(
        {
            "name": normalize_wxo_name(flow_definition.get("name") or ""),
            "id": str(flow_definition.get("id")),
        }
    )

    # Fallback for flows that don't include last_tested_version in payload
    if not flow_definition.get("last_tested_version"):
        detected_version = (get_version_info() or {}).get("version")
        if not detected_version:
            msg = "Unable to determine running Langflow version for snapshot creation."
            raise InvalidContentError(message=msg)
        flow_definition["last_tested_version"] = detected_version

    tool: LangflowTool = create_langflow_tool(
        tool_definition=flow_definition,
        connections=connections,
        show_details=True,
        # TODO: show_details is only set to true because the adk
        # has a bug where it fails to create requirements
        # when it is set to False.
        # Reset to False when the bug is fixed in the adk.
        # Even better, for us, remove this parameter entirely
        # and just default to False internally and not expose
        # it to the caller.
    )

    tool_payload = tool.__tool_spec__.model_dump(
        mode="json",
        exclude_unset=True,
        exclude_none=True,
        by_alias=True,
    )

    current_name = str(tool_payload.get("name") or "").strip()
    if current_name:
        tool_payload["name"] = normalize_wxo_name(current_name)

    (tool_payload.setdefault("binding", {}).setdefault("langflow", {})["project_id"]) = project_id
    logger.debug(
        "create_wxo_flow_tool: tool name='%s', project_id='%s', binding=%s",
        tool_payload.get("name"),
        project_id,
        tool_payload.get("binding", {}).get("langflow"),
    )

    artifacts: bytes = build_langflow_artifact_bytes(
        tool=tool,
        flow_definition=flow_definition,
    )

    return tool_payload, artifacts