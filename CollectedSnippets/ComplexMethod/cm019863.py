async def setup_backup_integration(
    hass: HomeAssistant,
    with_hassio: bool = False,
    *,
    backups: dict[str, list[AgentBackup]] | None = None,
    remote_agents: list[str] | None = None,
) -> dict[str, Mock]:
    """Set up the Backup integration."""
    backups = backups or {}
    with (
        patch("homeassistant.components.backup.is_hassio", return_value=with_hassio),
        patch(
            "homeassistant.components.backup.backup.is_hassio", return_value=with_hassio
        ),
        patch(
            "homeassistant.components.backup.services.is_hassio",
            return_value=with_hassio,
        ),
    ):
        remote_agents = remote_agents or []
        remote_agents_dict = {}
        for agent in remote_agents:
            if not agent.startswith(f"{TEST_DOMAIN}."):
                raise ValueError(f"Invalid agent_id: {agent}")
            name = agent.partition(".")[2]
            remote_agents_dict[agent] = mock_backup_agent(name, backups.get(agent))
        if remote_agents:
            platform = Mock(
                async_get_backup_agents=AsyncMock(
                    return_value=list(remote_agents_dict.values())
                ),
                spec_set=BackupAgentPlatformProtocol,
            )
            await setup_backup_platform(hass, domain=TEST_DOMAIN, platform=platform)

        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        if LOCAL_AGENT_ID not in backups or with_hassio:
            return remote_agents_dict

        local_agent = cast(
            CoreLocalBackupAgent, hass.data[DATA_MANAGER].backup_agents[LOCAL_AGENT_ID]
        )

        for backup in backups[LOCAL_AGENT_ID]:
            await local_agent.async_upload_backup(
                open_stream=AsyncMock(
                    side_effect=RuntimeError("Local agent does not open stream")
                ),
                backup=backup,
                on_progress=lambda *, on_progress, **_: None,
            )
        local_agent._loaded_backups = True

        return remote_agents_dict