async def async_delete_backup(
        self, backup_id: str, *, agent_ids: list[str] | None = None
    ) -> dict[str, Exception]:
        """Delete a backup."""
        agent_errors: dict[str, Exception] = {}
        if agent_ids is None:
            agent_ids = list(self.backup_agents)

        delete_backup_results = await asyncio.gather(
            *(
                self.backup_agents[agent_id].async_delete_backup(backup_id)
                for agent_id in agent_ids
            ),
            return_exceptions=True,
        )
        for idx, result in enumerate(delete_backup_results):
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

        if not agent_errors:
            self.known_backups.remove(backup_id)

        return agent_errors