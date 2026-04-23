async def apply_provider_update_plan_with_rollback(
    *,
    clients: WxOClient,
    user_id: IdLike,
    db: AsyncSession,
    agent_id: str,
    agent: dict[str, Any],
    update_payload: dict[str, Any],
    plan: ProviderUpdatePlan,
) -> WatsonxProviderUpdateApplyResult:
    """Apply provider_data update operations with rollback protection."""
    logger.debug(
        "apply_provider_update_plan: agent_id='%s', %d raw tools, %d renames, %d connection deltas, %d raw connections",
        agent_id,
        len(plan.raw_tools_to_create),
        len(plan.tool_renames),
        len(plan.existing_tool_deltas),
        len(plan.raw_connections_to_create),
    )
    # Rollback journals — tracked so partial failures can undo side-effects:
    # - created_tool_ids: provider tool ids created during this update.
    # - created_app_ids: provider app ids created during this update.
    # - original_tools: writable pre-update payloads for mutated existing tools.
    created_tool_ids: list[str] = []
    created_app_ids: list[str] = []
    original_tools: dict[str, dict[str, Any]] = {}

    # Working state:
    # - resolved_connections: provider_app_id → connection_id map for bind/update calls.
    # - operation_to_provider_app_id: operation app_id → provider app_id
    #     (identity mapping for both existing and raw-created connections).
    # - created_snapshot_ids: snapshot/tool ids created during this update.
    # - added_snapshot_ids: snapshot/tool ids newly attached to the agent by
    #     this update (created + newly attached existing).
    # - created_snapshot_bindings: source_ref ↔ tool_id bindings for newly
    #     created tools (created=True).
    # - added_snapshot_bindings: source_ref ↔ tool_id bindings for newly
    #     attached tools (created + newly attached existing).
    # - removed_snapshot_bindings: source_ref ↔ tool_id bindings detached from
    #     the agent by this update.
    # - referenced_snapshot_bindings: full operation correlation set.
    # - final_update_payload: outbound agent patch payload (spec + tools).
    # - rollback_agent_payload: best-effort restore payload for agent rollback.
    resolved_connections: dict[str, str] = {}
    operation_to_provider_app_id: dict[str, str] = {app_id: app_id for app_id in plan.existing_app_ids}
    created_snapshot_ids: list[str] = []
    added_snapshot_ids: list[str] = []
    created_snapshot_bindings: list[WatsonxResultToolRefBinding] = []
    final_update_payload = dict(update_payload)
    rollback_agent_payload: dict[str, Any] = {}

    # Pre-seed resolved_connections with bindings already attached to the
    # agent's existing tools.  This lets new tools reuse the same connections
    # without the caller having to redeclare them in the update payload, and
    # ensures they are checked first during resolution.
    #
    # Edge cases:
    # - Connection deleted in wxO but still in tool binding: the stale
    #   connection_id is pre-seeded here. If a new operation explicitly
    #   references this app_id, resolve_connections_for_operations will
    #   re-validate it and fail fast. If no operation references it, the
    #   stale entry is harmless (unused).
    # - Tool deleted in wxO but still in agent.tools: get_drafts_by_ids
    #   silently omits missing tools, so we just get fewer bindings.
    # - Multiple tools share the same app_id: setdefault keeps the first
    #   connection_id seen. All tools should agree on the mapping, but if
    #   they diverge, the explicit operation result will overwrite it.
    agent_tool_ids = extract_agent_tool_ids(agent)
    if agent_tool_ids:
        existing_tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, agent_tool_ids)
        for tool in existing_tools or []:
            if not isinstance(tool, dict):
                continue
            for app_id, connection_id in extract_langflow_connections_binding(tool).items():
                if app_id and connection_id:
                    operation_to_provider_app_id.setdefault(app_id, app_id)
                    resolved_connections.setdefault(app_id, connection_id)
        logger.debug(
            "apply_provider_update_plan: pre-seeded %d connections from %d agent tools",
            len(resolved_connections),
            len(agent_tool_ids),
        )

    try:
        try:
            connection_result = await resolve_connections_for_operations(
                clients=clients,
                user_id=user_id,
                db=db,
                existing_app_ids=plan.existing_app_ids,
                raw_connections_to_create=plan.raw_connections_to_create,
                error_prefix=ErrorPrefix.UPDATE.value,
                validate_connection_fn=validate_connection,
                create_connection_fn=create_connection_with_conflict_mapping,
            )
            operation_to_provider_app_id.update(connection_result.operation_to_provider_app_id)
            resolved_connections.update(connection_result.resolved_connections)
            created_app_ids.extend(connection_result.created_app_ids)
        except ConnectionCreateBatchError as exc:
            created_app_ids.extend(exc.created_app_ids)
            log_batch_errors(error_label="Connection create batch error", errors=exc.errors)
            raise exc.errors[0] from exc

        try:
            tool_create_result = await create_raw_tools_with_bindings(
                clients=clients,
                raw_tools_to_create=plan.raw_tools_to_create,
                operation_to_provider_app_id=operation_to_provider_app_id,
                resolved_connections=resolved_connections,
                create_and_upload_tools_fn=create_and_upload_wxo_flow_tools_with_bindings,
            )
            created_tool_ids.extend(tool_create_result.created_tool_ids)
            created_snapshot_ids.extend(tool_create_result.created_tool_ids)
            added_snapshot_ids.extend(tool_create_result.created_tool_ids)
            created_snapshot_bindings.extend(tool_create_result.snapshot_bindings)
        except ToolUploadBatchError as exc:
            created_tool_ids.extend(exc.created_tool_ids)
            created_snapshot_ids.extend(exc.created_tool_ids)
            added_snapshot_ids.extend(exc.created_tool_ids)
            log_batch_errors(error_label="Tool upload batch error", errors=exc.errors)
            raise exc.errors[0] from exc

        if plan.existing_tool_deltas:
            await _update_existing_tool_connection_deltas(
                clients=clients,
                existing_tool_deltas=plan.existing_tool_deltas,
                resolved_connections=resolved_connections,
                operation_to_provider_app_id=operation_to_provider_app_id,
                original_tools=original_tools,
            )

        if plan.tool_renames:
            await _apply_tool_renames(
                clients=clients,
                agent_tool_ids=extract_agent_tool_ids(agent),
                tool_renames=plan.tool_renames,
                original_tools=original_tools,
            )

        added_snapshot_ids.extend(ref.tool_id for ref in plan.added_existing_tool_refs)
        final_tools = dedupe_list([*plan.final_existing_tool_ids, *created_tool_ids])
        final_update_payload["tools"] = final_tools
        rollback_agent_payload = _build_agent_rollback_payload(
            agent=agent,
            final_update_payload=final_update_payload,
        )
        if final_update_payload:
            await retry_update(asyncio.to_thread, clients.agent.update, agent_id, final_update_payload)
    except Exception:
        logger.warning(
            "Provider update failed for agent_id=%s — initiating rollback (tools=%s, apps=%s)",
            agent_id,
            created_tool_ids,
            created_app_ids,
        )
        await _rollback_agent_update(
            clients=clients,
            agent_id=agent_id,
            rollback_agent_payload=rollback_agent_payload,
        )
        await rollback_update_resources(
            clients=clients,
            created_tool_ids=created_tool_ids,
            created_app_id=None,
            original_tools=original_tools,
        )
        await rollback_created_app_ids(
            clients=clients,
            created_app_ids=created_app_ids,
        )
        raise

    return WatsonxProviderUpdateApplyResult(
        created_app_ids=dedupe_list(created_app_ids),
        created_snapshot_ids=dedupe_list(created_snapshot_ids),
        added_snapshot_ids=dedupe_list(added_snapshot_ids),
        created_snapshot_bindings=created_snapshot_bindings,
        added_snapshot_bindings=[*plan.added_existing_tool_refs, *created_snapshot_bindings],
        removed_snapshot_bindings=plan.removed_existing_tool_refs,
        referenced_snapshot_bindings=[*plan.existing_tool_refs, *created_snapshot_bindings],
    )