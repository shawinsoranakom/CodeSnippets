async def _async_create_backup(
        self,
        *,
        agent_ids: list[str],
        extra_metadata: dict[str, bool | str] | None,
        include_addons: list[str] | None,
        include_all_addons: bool,
        include_database: bool,
        include_folders: list[Folder] | None,
        include_homeassistant: bool,
        name: str | None,
        password: str | None,
        raise_task_error: bool,
        with_automatic_settings: bool,
    ) -> NewBackup:
        """Initiate generating a backup."""
        unavailable_agents = [
            agent_id for agent_id in agent_ids if agent_id not in self.backup_agents
        ]
        if not (
            available_agents := [
                agent_id for agent_id in agent_ids if agent_id in self.backup_agents
            ]
        ):
            raise BackupManagerError(
                f"At least one available backup agent must be selected, got {agent_ids}"
            )
        if unavailable_agents:
            LOGGER.warning(
                "Backup agents %s are not available, will backup to %s",
                unavailable_agents,
                available_agents,
            )
        if include_all_addons and include_addons:
            raise BackupManagerError(
                "Cannot include all addons and specify specific addons"
            )

        backup_name = (
            (name if name is None else name.strip())
            or f"{'Automatic' if with_automatic_settings else 'Custom'} backup {HAVERSION}"
        )
        extra_metadata = extra_metadata or {}

        try:
            (
                new_backup,
                self._backup_task,
            ) = await self._reader_writer.async_create_backup(
                agent_ids=available_agents,
                backup_name=backup_name,
                extra_metadata=extra_metadata
                | {
                    "instance_id": await instance_id.async_get(self.hass),
                    "with_automatic_settings": with_automatic_settings,
                },
                include_addons=include_addons,
                include_all_addons=include_all_addons,
                include_database=include_database,
                include_folders=include_folders,
                include_homeassistant=include_homeassistant,
                on_progress=self.async_on_backup_event,
                password=password,
            )
        except BackupReaderWriterError as err:
            raise BackupManagerError(str(err)) from err

        backup_finish_task = self._backup_finish_task = self.hass.async_create_task(
            self._async_finish_backup(
                available_agents, unavailable_agents, with_automatic_settings, password
            ),
            name="backup_manager_finish_backup",
        )
        if not raise_task_error:

            def log_finish_task_error(task: asyncio.Task[None]) -> None:
                if task.done() and not task.cancelled() and (err := task.exception()):
                    if isinstance(err, BackupManagerError):
                        LOGGER.error("Error creating backup: %s", err)
                    else:
                        LOGGER.error("Unexpected error: %s", err, exc_info=err)

            backup_finish_task.add_done_callback(log_finish_task_error)

        return new_backup