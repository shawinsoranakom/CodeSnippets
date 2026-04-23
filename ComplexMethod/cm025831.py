def _delete_filter(
        backups: dict[str, ManagerBackup],
    ) -> dict[str, ManagerBackup]:
        """Return oldest backups more numerous than copies to delete."""
        agents_retention = {
            agent_id: agent_config.retention
            for agent_id, agent_config in manager.config.data.agents.items()
        }
        has_agents_retention = any(
            agent_retention for agent_retention in agents_retention.values()
        )
        has_agents_retention_copies = any(
            agent_retention and agent_retention.copies is not None
            for agent_retention in agents_retention.values()
        )
        # we need to check here since we await before
        # this filter is applied
        if (
            global_copies := manager.config.data.retention.copies
        ) is None and not has_agents_retention_copies:
            # No global retention copies and no agent retention copies
            return {}
        if global_copies is not None and not has_agents_retention:
            # Return early to avoid the longer filtering below.
            return dict(
                sorted(
                    backups.items(),
                    key=lambda backup_item: backup_item[1].date,
                )[: max(len(backups) - global_copies, 0)]
            )

        backups_by_agent: dict[str, dict[str, ManagerBackup]] = defaultdict(dict)
        for backup_id, backup in backups.items():
            for agent_id in backup.agents:
                backups_by_agent[agent_id][backup_id] = backup

        backups_to_delete_by_agent: dict[str, dict[str, ManagerBackup]] = defaultdict(
            dict
        )
        for agent_id, agent_backups in backups_by_agent.items():
            agent_retention = agents_retention.get(agent_id)
            if agent_retention is None:
                # This agent does not have a retention setting,
                # so the global retention setting should be used.
                if global_copies is None:
                    # This agent does not have a retention setting
                    # and the global retention copies setting is None,
                    # so backups should not be deleted.
                    continue
                # The global retention setting will be used.
                copies = global_copies
            elif (agent_copies := agent_retention.copies) is None:
                # This agent has a retention setting
                # where copies is set to None,
                # so backups should not be deleted.
                continue
            else:
                # This agent retention setting will be used.
                copies = agent_copies

            backups_to_delete_by_agent[agent_id] = dict(
                sorted(
                    agent_backups.items(),
                    key=lambda backup_item: backup_item[1].date,
                )[: max(len(agent_backups) - copies, 0)]
            )

        backup_ids_to_delete: dict[str, set[str]] = defaultdict(set)
        for agent_id, to_delete in backups_to_delete_by_agent.items():
            for backup_id in to_delete:
                backup_ids_to_delete[backup_id].add(agent_id)
        backups_to_delete: dict[str, ManagerBackup] = {}
        for backup_id, agent_ids in backup_ids_to_delete.items():
            backup = backups[backup_id]
            # filter the backup to only include the agents that should be deleted
            filtered_backup = replace(
                backup,
                agents={
                    agent_id: agent_backup_status
                    for agent_id, agent_backup_status in backup.agents.items()
                    if agent_id in agent_ids
                },
            )
            backups_to_delete[backup_id] = filtered_backup
        return backups_to_delete