def _delete_filter(
                backups: dict[str, ManagerBackup],
            ) -> dict[str, ManagerBackup]:
                """Return backups older than days to delete."""
                # we need to check here since we await before
                # this filter is applied
                agents_retention = {
                    agent_id: agent_config.retention
                    for agent_id, agent_config in manager.config.data.agents.items()
                }
                has_agents_retention = any(
                    agent_retention for agent_retention in agents_retention.values()
                )
                has_agents_retention_days = any(
                    agent_retention and agent_retention.days is not None
                    for agent_retention in agents_retention.values()
                )
                if (global_days := self.days) is None and not has_agents_retention_days:
                    # No global retention days and no agent retention days
                    return {}

                now = dt_util.utcnow()
                if global_days is not None and not has_agents_retention:
                    # Return early to avoid the longer filtering below.
                    return {
                        backup_id: backup
                        for backup_id, backup in backups.items()
                        if dt_util.parse_datetime(backup.date, raise_on_error=True)
                        + timedelta(days=global_days)
                        < now
                    }

                # If there are any agent retention settings, we need to check
                # the retention settings, for every backup and agent combination.

                backups_to_delete = {}

                for backup_id, backup in backups.items():
                    backup_date = dt_util.parse_datetime(
                        backup.date, raise_on_error=True
                    )
                    delete_from_agents = set(backup.agents)
                    for agent_id in backup.agents:
                        agent_retention = agents_retention.get(agent_id)
                        if agent_retention is None:
                            # This agent does not have a retention setting,
                            # so the global retention setting should be used.
                            if global_days is None:
                                # This agent does not have a retention setting
                                # and the global retention days setting is None,
                                # so this backup should not be deleted.
                                delete_from_agents.discard(agent_id)
                                continue
                            days = global_days
                        elif (agent_days := agent_retention.days) is None:
                            # This agent has a retention setting
                            # where days is set to None,
                            # so the backup should not be deleted.
                            delete_from_agents.discard(agent_id)
                            continue
                        else:
                            # This agent has a retention setting
                            # where days is set to a number,
                            # so that setting should be used.
                            days = agent_days
                        if backup_date + timedelta(days=days) >= now:
                            # This backup is not older than the retention days,
                            # so this agent should not be deleted.
                            delete_from_agents.discard(agent_id)

                    filtered_backup = replace(
                        backup,
                        agents={
                            agent_id: agent_backup_status
                            for agent_id, agent_backup_status in backup.agents.items()
                            if agent_id in delete_from_agents
                        },
                    )
                    backups_to_delete[backup_id] = filtered_backup

                return backups_to_delete