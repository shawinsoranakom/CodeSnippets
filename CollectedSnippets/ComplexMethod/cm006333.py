def build_provider_update_plan(
    *,
    agent: dict[str, Any],
    provider_update: WatsonxDeploymentUpdatePayload,
) -> ProviderUpdatePlan:
    """Build a deterministic CPU-only plan for provider_data update operations."""
    # put_tools is a standalone full replacement of the agent's tool list
    # (no operations accompany it).
    if provider_update.put_tools is not None:
        return ProviderUpdatePlan(
            existing_app_ids=[],
            raw_connections_to_create=[],
            existing_tool_deltas={},
            raw_tools_to_create=[],
            tool_renames={},
            final_existing_tool_ids=list(dict.fromkeys(provider_update.put_tools)),
            added_existing_tool_refs=[],
            removed_existing_tool_refs=[],
            existing_tool_refs=[],
        )

    agent_tool_ids = extract_agent_tool_ids(agent)
    final_existing_tool_ids = OrderedUniqueStrs.from_values(agent_tool_ids)

    # existing_tool_deltas: per existing tool_id, tracks app_ids to bind/unbind.
    existing_tool_deltas: dict[str, ToolConnectionOps] = {}
    # added_existing_tool_refs: existing refs newly attached to this agent by
    #   bind(existing)/attach_tool operations (i.e. not in agent_tool_ids at
    #   plan start).
    added_existing_tool_refs: list[WatsonxResultToolRefBinding] = []
    # removed_existing_tool_refs: existing refs detached by remove_tool.
    removed_existing_tool_refs: list[WatsonxResultToolRefBinding] = []
    # raw_tool_app_ids: per raw tool name, collects operation app_ids to bind
    #   when the raw tool is created. Initialize with all declared raw tools so
    #   unbound tools are still created and attached with empty connections.
    raw_tool_app_ids: dict[str, OrderedUniqueStrs] = {
        raw_payload.name: OrderedUniqueStrs() for raw_payload in (provider_update.tools.raw_payloads or [])
    }
    # operation_app_ids: every app_id referenced by bind/unbind operations.
    #   Used later to derive existing_app_ids by subtracting raw connection
    #   app_ids declared in connections.raw_payloads.
    operation_app_ids = OrderedUniqueStrs()
    # existing_tool_refs: source_ref ↔ tool_id correlations (created=False)
    #   collected from all operations that reference existing tools (bind,
    #   unbind, remove_tool). Deduped by tool_id before storing in the plan,
    #   then merged directly into the update result alongside newly-created
    #   snapshot bindings.
    existing_tool_refs: list[WatsonxResultToolRefBinding] = []
    # tool_renames: tool_id → new_name for rename_tool operations.
    tool_renames: dict[str, str] = {}

    for operation in provider_update.operations:
        if isinstance(operation, WatsonxBindOperation):
            operation_app_ids.extend(operation.app_ids)
            if operation.tool.tool_id_with_ref is not None:
                ref = operation.tool.tool_id_with_ref
                tool_id = ref.tool_id
                if tool_id not in agent_tool_ids:
                    added_existing_tool_refs.append(
                        WatsonxResultToolRefBinding(source_ref=ref.source_ref, tool_id=tool_id, created=False)
                    )
                final_existing_tool_ids.add(tool_id)
                existing_tool_refs.append(
                    WatsonxResultToolRefBinding(source_ref=ref.source_ref, tool_id=tool_id, created=False)
                )
                if operation.app_ids:
                    delta = _get_or_create_tool_connection_ops(existing_tool_deltas, tool_id=tool_id)
                    delta.bind.extend(operation.app_ids)
                continue

            raw_name = str(operation.tool.name_of_raw)
            raw_apps = raw_tool_app_ids.setdefault(raw_name, OrderedUniqueStrs())
            raw_apps.extend(operation.app_ids)
            continue

        if isinstance(operation, WatsonxAttachToolOperation):
            tool_id = operation.tool.tool_id
            if tool_id not in agent_tool_ids:
                added_existing_tool_refs.append(
                    WatsonxResultToolRefBinding(source_ref=operation.tool.source_ref, tool_id=tool_id, created=False)
                )
            final_existing_tool_ids.add(tool_id)
            existing_tool_refs.append(
                WatsonxResultToolRefBinding(source_ref=operation.tool.source_ref, tool_id=tool_id, created=False)
            )
            continue

        if isinstance(operation, WatsonxUnbindOperation):
            operation_app_ids.extend(operation.app_ids)
            tool_id = operation.tool.tool_id
            existing_tool_refs.append(
                WatsonxResultToolRefBinding(source_ref=operation.tool.source_ref, tool_id=tool_id, created=False)
            )
            delta = _get_or_create_tool_connection_ops(existing_tool_deltas, tool_id=tool_id)
            delta.unbind.extend(operation.app_ids)
            continue

        if isinstance(operation, WatsonxRenameToolOperation):
            tool_renames[operation.tool.tool_id] = operation.new_name
            existing_tool_refs.append(
                WatsonxResultToolRefBinding(
                    source_ref=operation.tool.source_ref, tool_id=operation.tool.tool_id, created=False
                )
            )
            continue

        if isinstance(operation, WatsonxRemoveToolOperation):
            removed_ref = WatsonxResultToolRefBinding(
                source_ref=operation.tool.source_ref,
                tool_id=operation.tool.tool_id,
                created=False,
            )
            removed_existing_tool_refs.append(removed_ref)
            existing_tool_refs.append(removed_ref)
            final_existing_tool_ids.discard(operation.tool.tool_id)
            continue

    raw_connections_to_create = [
        RawConnectionCreatePlan(
            operation_app_id=raw_payload.app_id,
            provider_app_id=raw_payload.app_id,
            payload=raw_payload,
        )
        for raw_payload in (provider_update.connections.raw_payloads or [])
    ]

    raw_tool_pool = {raw_payload.name: raw_payload for raw_payload in (provider_update.tools.raw_payloads or [])}
    raw_tools_to_create = [
        RawToolCreatePlan(raw_name=raw_name, payload=raw_tool_pool[raw_name], app_ids=app_ids.to_list())
        for raw_name, app_ids in raw_tool_app_ids.items()
    ]

    seen_ref_ids: dict[str, WatsonxResultToolRefBinding] = {}
    for ref in existing_tool_refs:
        seen_ref_ids.setdefault(ref.tool_id, ref)
    deduped_existing_tool_refs = list(seen_ref_ids.values())

    seen_added_ref_ids: dict[str, WatsonxResultToolRefBinding] = {}
    for ref in added_existing_tool_refs:
        seen_added_ref_ids.setdefault(ref.tool_id, ref)
    deduped_added_existing_tool_refs = list(seen_added_ref_ids.values())

    seen_removed_ref_ids: dict[str, WatsonxResultToolRefBinding] = {}
    for ref in removed_existing_tool_refs:
        seen_removed_ref_ids.setdefault(ref.tool_id, ref)
    deduped_removed_existing_tool_refs = list(seen_removed_ref_ids.values())

    raw_app_ids = {raw_payload.app_id for raw_payload in (provider_update.connections.raw_payloads or [])}
    existing_app_ids = [app_id for app_id in operation_app_ids.to_list() if app_id not in raw_app_ids]

    return ProviderUpdatePlan(
        existing_app_ids=existing_app_ids,
        raw_connections_to_create=raw_connections_to_create,
        existing_tool_deltas=existing_tool_deltas,
        raw_tools_to_create=raw_tools_to_create,
        tool_renames=tool_renames,
        final_existing_tool_ids=final_existing_tool_ids.to_list(),
        added_existing_tool_refs=deduped_added_existing_tool_refs,
        removed_existing_tool_refs=deduped_removed_existing_tool_refs,
        existing_tool_refs=deduped_existing_tool_refs,
    )