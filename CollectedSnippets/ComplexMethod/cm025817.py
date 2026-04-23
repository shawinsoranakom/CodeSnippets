async def async_get_backups(
        self,
    ) -> tuple[dict[str, ManagerBackup], dict[str, Exception]]:
        """Get backups.

        Return a dictionary of Backup instances keyed by their ID.
        """
        backups: dict[str, ManagerBackup] = {}
        agent_errors: dict[str, Exception] = {}
        agent_ids = list(self.backup_agents)

        list_backups_results = await asyncio.gather(
            *(agent.async_list_backups() for agent in self.backup_agents.values()),
            return_exceptions=True,
        )
        for idx, result in enumerate(list_backups_results):
            agent_id = agent_ids[idx]
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
            for agent_backup in result:
                if (backup_id := agent_backup.backup_id) not in backups:
                    if known_backup := self.known_backups.get(backup_id):
                        failed_addons = known_backup.failed_addons
                        failed_agent_ids = known_backup.failed_agent_ids
                        failed_folders = known_backup.failed_folders
                    else:
                        failed_addons = []
                        failed_agent_ids = []
                        failed_folders = []
                    with_automatic_settings = self.is_our_automatic_backup(
                        agent_backup, await instance_id.async_get(self.hass)
                    )
                    backups[backup_id] = ManagerBackup(
                        agents={},
                        addons=agent_backup.addons,
                        backup_id=backup_id,
                        date=agent_backup.date,
                        database_included=agent_backup.database_included,
                        extra_metadata=agent_backup.extra_metadata,
                        failed_addons=failed_addons,
                        failed_agent_ids=failed_agent_ids,
                        failed_folders=failed_folders,
                        folders=agent_backup.folders,
                        homeassistant_included=agent_backup.homeassistant_included,
                        homeassistant_version=agent_backup.homeassistant_version,
                        name=agent_backup.name,
                        with_automatic_settings=with_automatic_settings,
                    )
                backups[backup_id].agents[agent_id] = AgentBackupStatus(
                    protected=agent_backup.protected,
                    size=agent_backup.size,
                )

        return (backups, agent_errors)