def check_unavailable_agents(hass: HomeAssistant, manager: BackupManager) -> None:
    """Check for unavailable agents."""
    if missing_agent_ids := set(manager.config.data.create_backup.agent_ids) - set(
        manager.backup_agents
    ):
        LOGGER.debug(
            "Agents %s are configured for automatic backup but are unavailable",
            missing_agent_ids,
        )

    # Remove issues for unavailable agents that are not unavailable anymore.
    issue_registry = ir.async_get(hass)
    existing_missing_agent_issue_ids = {
        issue_id
        for domain, issue_id in issue_registry.issues
        if domain == DOMAIN
        and issue_id.startswith(AUTOMATIC_BACKUP_AGENTS_UNAVAILABLE_ISSUE_ID)
    }
    current_missing_agent_issue_ids = {
        f"{AUTOMATIC_BACKUP_AGENTS_UNAVAILABLE_ISSUE_ID}_{agent_id}": agent_id
        for agent_id in missing_agent_ids
    }
    for issue_id in existing_missing_agent_issue_ids - set(
        current_missing_agent_issue_ids
    ):
        ir.async_delete_issue(hass, DOMAIN, issue_id)
    for issue_id, agent_id in current_missing_agent_issue_ids.items():
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            learn_more_url="homeassistant://config/backup",
            severity=ir.IssueSeverity.WARNING,
            translation_key="automatic_backup_agents_unavailable",
            translation_placeholders={
                "agent_id": agent_id,
                "backup_settings": "/config/backup/settings",
            },
        )