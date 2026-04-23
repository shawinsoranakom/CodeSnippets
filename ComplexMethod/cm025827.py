async def async_validate_config(self, *, config: BackupConfig) -> None:
        """Validate backup config.

        Update automatic backup settings to not include addons or folders and remove
        hassio agents in case a backup created by supervisor was restored.
        """
        create_backup = config.data.create_backup
        if (
            not create_backup.include_addons
            and not create_backup.include_all_addons
            and not create_backup.include_folders
            and not any(a_id.startswith("hassio.") for a_id in create_backup.agent_ids)
        ):
            LOGGER.debug("Backup settings don't need to be adjusted")
            return

        LOGGER.info(
            "Adjusting backup settings to not include addons, folders or supervisor locations"
        )
        automatic_agents = [
            agent_id
            for agent_id in create_backup.agent_ids
            if not agent_id.startswith("hassio.")
        ]
        if (
            self._local_agent_id not in automatic_agents
            and "hassio.local" in create_backup.agent_ids
        ):
            automatic_agents = [self._local_agent_id, *automatic_agents]
        config.update(
            create_backup=CreateBackupParametersDict(
                agent_ids=automatic_agents,
                include_addons=None,
                include_all_addons=False,
                include_folders=None,
            )
        )