async def async_delete_filtered_backups(
        self,
        *,
        include_filter: Callable[[dict[str, ManagerBackup]], dict[str, ManagerBackup]],
        delete_filter: Callable[[dict[str, ManagerBackup]], dict[str, ManagerBackup]],
    ) -> None:
        """Delete backups parsed with a filter.

        :param include_filter: A filter that should return the backups to consider for
        deletion. Note: The newest of the backups returned by include_filter will
        unconditionally be kept, even if delete_filter returns all backups.
        :param delete_filter: A filter that should return the backups to delete.
        """
        backups, get_agent_errors = await self.async_get_backups()
        if get_agent_errors:
            LOGGER.debug(
                "Error getting backups; continuing anyway: %s",
                get_agent_errors,
            )

        # Run the include filter first to ensure we only consider backups that
        # should be included in the deletion process.
        backups = include_filter(backups)
        backups_by_agent: dict[str, dict[str, ManagerBackup]] = defaultdict(dict)
        for backup_id, backup in backups.items():
            for agent_id in backup.agents:
                backups_by_agent[agent_id][backup_id] = backup

        LOGGER.debug("Backups returned by include filter: %s", backups)
        LOGGER.debug(
            "Backups returned by include filter by agent: %s",
            {agent_id: list(backups) for agent_id, backups in backups_by_agent.items()},
        )

        backups_to_delete = delete_filter(backups)

        LOGGER.debug("Backups returned by delete filter: %s", backups_to_delete)

        if not backups_to_delete:
            return

        # always delete oldest backup first
        backups_to_delete_by_agent: dict[str, dict[str, ManagerBackup]] = defaultdict(
            dict
        )
        for backup_id, backup in sorted(
            backups_to_delete.items(),
            key=lambda backup_item: backup_item[1].date,
        ):
            for agent_id in backup.agents:
                backups_to_delete_by_agent[agent_id][backup_id] = backup
        LOGGER.debug(
            "Backups returned by delete filter by agent: %s",
            {
                agent_id: list(backups)
                for agent_id, backups in backups_to_delete_by_agent.items()
            },
        )
        for agent_id, to_delete_from_agent in backups_to_delete_by_agent.items():
            if len(to_delete_from_agent) >= len(backups_by_agent[agent_id]):
                # Never delete the last backup.
                last_backup = to_delete_from_agent.popitem()
                LOGGER.debug(
                    "Keeping the last backup %s for agent %s", last_backup, agent_id
                )

        LOGGER.debug(
            "Backups to delete by agent: %s",
            {
                agent_id: list(backups)
                for agent_id, backups in backups_to_delete_by_agent.items()
            },
        )

        backup_ids_to_delete: dict[str, set[str]] = defaultdict(set)
        for agent_id, to_delete in backups_to_delete_by_agent.items():
            for backup_id in to_delete:
                backup_ids_to_delete[backup_id].add(agent_id)

        if not backup_ids_to_delete:
            return

        backup_ids = list(backup_ids_to_delete)
        delete_results = await asyncio.gather(
            *(
                self.async_delete_backup(backup_id, agent_ids=list(agent_ids))
                for backup_id, agent_ids in backup_ids_to_delete.items()
            )
        )
        agent_errors = {
            backup_id: error
            for backup_id, error_dict in zip(backup_ids, delete_results, strict=True)
            for error in error_dict.values()
            if error and not isinstance(error, BackupNotFound)
        }
        if agent_errors:
            LOGGER.error(
                "Error deleting old copies: %s",
                agent_errors,
            )