async def async_get_backup(
        self, backup_id: str
    ) -> tuple[ManagerBackup | None, dict[str, Exception]]:
        """Get a backup."""
        backup: ManagerBackup | None = None
        agent_errors: dict[str, Exception] = {}
        agent_ids = list(self.backup_agents)

        get_backup_results = await asyncio.gather(
            *(
                agent.async_get_backup(backup_id)
                for agent in self.backup_agents.values()
            ),
            return_exceptions=True,
        )
        for idx, result in enumerate(get_backup_results):
            agent_id = agent_ids[idx]
            if isinstance(result, BackupNotFound):
                continue
            if isinstance(result, BackupAgentError):
                agent_errors[agent_id] = result
                continue
            if isinstance(result, Exception):
                agent_errors[agent_id] = result
                LOGGER.error(
                    "Unexpected error for %s: %s", agent_id, result, exc_info=result
                )
                continue
            if isinstance(result, BaseException):
                raise result  # unexpected error
            # Check for None to be backwards compatible with the old BackupAgent API,
            # this can be removed in HA Core 2025.10
            if not result:
                frame.report_usage(
                    "returns None from BackupAgent.async_get_backup",
                    breaks_in_ha_version="2025.10",
                    integration_domain=agent_id.partition(".")[0],
                )
                continue
            if backup is None:
                if known_backup := self.known_backups.get(backup_id):
                    failed_addons = known_backup.failed_addons
                    failed_agent_ids = known_backup.failed_agent_ids
                    failed_folders = known_backup.failed_folders
                else:
                    failed_addons = []
                    failed_agent_ids = []
                    failed_folders = []
                with_automatic_settings = self.is_our_automatic_backup(
                    result, await instance_id.async_get(self.hass)
                )
                backup = ManagerBackup(
                    agents={},
                    addons=result.addons,
                    backup_id=result.backup_id,
                    date=result.date,
                    database_included=result.database_included,
                    extra_metadata=result.extra_metadata,
                    failed_addons=failed_addons,
                    failed_agent_ids=failed_agent_ids,
                    failed_folders=failed_folders,
                    folders=result.folders,
                    homeassistant_included=result.homeassistant_included,
                    homeassistant_version=result.homeassistant_version,
                    name=result.name,
                    with_automatic_settings=with_automatic_settings,
                )
            backup.agents[agent_id] = AgentBackupStatus(
                protected=result.protected,
                size=result.size,
            )

        return (backup, agent_errors)