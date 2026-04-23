def build_provider_create_plan(
    *,
    deployment_name: str,
    provider_create: WatsonxDeploymentCreatePayload,
) -> ProviderCreatePlan:
    """Build a deterministic CPU-only plan for provider_data create operations."""
    normalized_deployment_name = validate_wxo_name(deployment_name)

    # existing_tool_ids: provider tool ids from bind operations that reference
    #   pre-existing tools (via tool_id_with_ref); included in the final agent.
    existing_tool_ids = OrderedUniqueStrs()
    # existing_tool_bindings: per existing tool_id, collects operation app_ids
    #   that should be bound to that tool during creation.
    existing_tool_bindings: dict[str, OrderedUniqueStrs] = {}
    # selected_operation_app_ids: all app_ids referenced by any bind operation
    #   (used to determine which connections the create plan needs).
    selected_operation_app_ids = OrderedUniqueStrs()

    # raw_tool_app_ids: per raw tool name, collects operation app_ids to bind
    #   when the raw tool is created.
    raw_tool_app_ids = {
        raw_payload.name: OrderedUniqueStrs() for raw_payload in (provider_create.tools.raw_payloads or [])
    }
    for operation in provider_create.operations:
        if isinstance(operation, WatsonxAttachToolOperation):
            existing_tool_ids.add(operation.tool.tool_id)
            continue
        if not isinstance(operation, WatsonxBindOperation):
            continue
        selected_operation_app_ids.extend(operation.app_ids)
        if operation.tool.tool_id_with_ref is not None:
            tool_id = operation.tool.tool_id_with_ref.tool_id
            existing_tool_ids.add(tool_id)
            if operation.app_ids:
                existing_bindings = existing_tool_bindings.setdefault(tool_id, OrderedUniqueStrs())
                existing_bindings.extend(operation.app_ids)
            continue
        raw_name = str(operation.tool.name_of_raw)
        raw_apps = raw_tool_app_ids.setdefault(raw_name, OrderedUniqueStrs())
        raw_apps.extend(operation.app_ids)

    raw_app_ids = {raw_payload.app_id for raw_payload in (provider_create.connections.raw_payloads or [])}
    existing_app_ids = OrderedUniqueStrs.from_values(
        [app_id for app_id in selected_operation_app_ids.to_list() if app_id not in raw_app_ids]
    )

    raw_connections_to_create = [
        RawConnectionCreatePlan(
            operation_app_id=raw_payload.app_id,
            provider_app_id=raw_payload.app_id,
            payload=raw_payload,
        )
        for raw_payload in (provider_create.connections.raw_payloads or [])
    ]
    raw_tool_pool = {raw_payload.name: raw_payload for raw_payload in (provider_create.tools.raw_payloads or [])}
    raw_tools_to_create = [
        RawToolCreatePlan(raw_name=raw_name, payload=raw_tool_pool[raw_name], app_ids=app_ids.to_list())
        for raw_name, app_ids in raw_tool_app_ids.items()
    ]

    return ProviderCreatePlan(
        deployment_name=normalized_deployment_name,
        llm=provider_create.llm,
        existing_tool_ids=existing_tool_ids.to_list(),
        existing_tool_bindings={tool_id: app_ids.to_list() for tool_id, app_ids in existing_tool_bindings.items()},
        existing_app_ids=existing_app_ids.to_list(),
        raw_connections_to_create=raw_connections_to_create,
        raw_tools_to_create=raw_tools_to_create,
        selected_operation_app_ids=selected_operation_app_ids.to_list(),
    )