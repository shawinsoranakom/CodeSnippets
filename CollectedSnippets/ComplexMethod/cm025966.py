async def async_restore_backup(
        self,
        backup_id: str,
        *,
        agent_id: str,
        on_progress: Callable[[RestoreBackupEvent], None],
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        password: str | None,
        restore_addons: list[str] | None,
        restore_database: bool,
        restore_folders: list[Folder] | None,
        restore_homeassistant: bool,
    ) -> None:
        """Restore a backup."""
        manager = self._hass.data[DATA_MANAGER]
        # The backup manager has already checked that the backup exists so we don't
        # need to catch BackupNotFound here.
        backup = await manager.backup_agents[agent_id].async_get_backup(backup_id)
        if (
            # Check for None to be backwards compatible with the old BackupAgent API,
            # this can be removed in HA Core 2025.10
            backup
            and restore_homeassistant
            and restore_database != backup.database_included
        ):
            raise HomeAssistantError("Restore database must match backup")
        if not restore_homeassistant and restore_database:
            raise HomeAssistantError("Cannot restore database without Home Assistant")
        restore_addons_set = set(restore_addons) if restore_addons else None
        restore_folders_set = (
            {supervisor_backups.Folder(folder) for folder in restore_folders}
            if restore_folders
            else None
        )

        restore_location: str
        if manager.backup_agents[agent_id].domain != DOMAIN:
            # Download the backup to the supervisor. Supervisor will clean up the backup
            # two days after the restore is done.
            await self.async_receive_backup(
                agent_ids=[],
                stream=await open_stream(),
                suggested_filename=f"{backup_id}.tar",
            )
            restore_location = LOCATION_CLOUD_BACKUP
        else:
            agent = cast(SupervisorBackupAgent, manager.backup_agents[agent_id])
            restore_location = agent.location

        try:
            job = await self._client.backups.partial_restore(
                backup_id,
                supervisor_backups.PartialRestoreOptions(
                    addons=restore_addons_set,
                    folders=restore_folders_set,
                    homeassistant=restore_homeassistant,
                    password=password,
                    background=True,
                    location=restore_location,
                ),
            )
        except SupervisorNotFoundError as err:
            raise BackupNotFound from err
        except SupervisorBadRequestError as err:
            # Supervisor currently does not transmit machine parsable error types
            message = err.args[0]
            if message.startswith("Invalid password for backup"):
                raise IncorrectPasswordError(message) from err
            raise HomeAssistantError(message) from err

        restore_complete = asyncio.Event()
        restore_errors: list[dict[str, str]] = []

        @callback
        def on_job_progress(data: Mapping[str, Any]) -> None:
            """Handle backup restore progress."""
            if not (stage := try_parse_enum(RestoreBackupStage, data.get("stage"))):
                _LOGGER.debug("Unknown restore stage: %s", data.get("stage"))
            else:
                on_progress(
                    RestoreBackupEvent(
                        reason=None, stage=stage, state=RestoreBackupState.IN_PROGRESS
                    )
                )
            if data.get("done") is True:
                restore_complete.set()
                restore_errors.extend(data.get("errors", []))

        unsub = self._async_listen_job_events(job.job_id, on_job_progress)
        try:
            await self._get_job_state(job.job_id, on_job_progress)
            await restore_complete.wait()
            if restore_errors:
                # We should add more specific error handling here in the future
                raise BackupReaderWriterError(f"Restore failed: {restore_errors}")
        finally:
            unsub()