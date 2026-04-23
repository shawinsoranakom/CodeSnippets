async def rollback_created_resources(
    *,
    clients: WxOClient,
    agent_id: str | None,
    tool_ids: list[str],
    app_ids: list[str] | None = None,
) -> None:
    app_ids_to_rollback = list(app_ids or [])
    logger.info(
        "Rolling back resources: agent_id=%s, tool_ids=%s, app_ids=%s",
        agent_id,
        tool_ids,
        app_ids_to_rollback,
    )
    if agent_id:
        try:
            await retry_rollback(delete_agent_if_exists, clients, agent_id=agent_id)
        except Exception:  # noqa: BLE001
            logger.exception("Rollback failed for agent_id=%s — resource may be orphaned", agent_id)
    if tool_ids:
        for tool_id in reversed(tool_ids):
            try:
                await retry_rollback(delete_tool_if_exists, clients, tool_id=tool_id)
            except Exception:  # noqa: BLE001
                logger.exception("Rollback failed for tool_id=%s — resource may be orphaned", tool_id)
    for created_app_id in reversed(app_ids_to_rollback):
        try:
            await retry_rollback(delete_config_if_exists, clients, app_id=created_app_id)
        except Exception:  # noqa: BLE001
            logger.exception("Rollback failed for app_id=%s — resource may be orphaned", created_app_id)