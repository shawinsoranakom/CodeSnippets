async def _async_finish_backup(
        self,
        available_agents: list[str],
        unavailable_agents: list[str],
        with_automatic_settings: bool,
        password: str | None,
    ) -> None:
        """Finish a backup."""
        if TYPE_CHECKING:
            assert self._backup_task is not None
        backup_success = False
        try:
            written_backup = await self._backup_task
        except Exception as err:
            if with_automatic_settings:
                self._update_issue_backup_failed()

            if isinstance(err, BackupReaderWriterError):
                raise BackupManagerError(str(err)) from err
            raise  # unexpected error
        else:
            LOGGER.debug(
                "Generated new backup with backup_id %s, uploading to agents %s",
                written_backup.backup.backup_id,
                available_agents,
            )
            self.async_on_backup_event(
                CreateBackupEvent(
                    reason=None,
                    stage=CreateBackupStage.UPLOAD_TO_AGENTS,
                    state=CreateBackupState.IN_PROGRESS,
                )
            )

            try:
                agent_errors = await self._async_upload_backup(
                    backup=written_backup.backup,
                    agent_ids=available_agents,
                    open_stream=written_backup.open_stream,
                    password=password,
                )
            finally:
                await written_backup.release_stream()
            self.known_backups.add(
                written_backup.backup,
                agent_errors,
                written_backup.addon_errors,
                written_backup.folder_errors,
                unavailable_agents,
            )
            if not agent_errors:
                if with_automatic_settings:
                    # create backup was successful, update last_completed_automatic_backup
                    self.config.data.last_completed_automatic_backup = dt_util.now()
                    self.store.save()
                backup_success = True

            if with_automatic_settings:
                self._update_issue_after_agent_upload(
                    written_backup, agent_errors, unavailable_agents
                )
            # delete old backups more numerous than copies
            # try this regardless of agent errors above
            self.async_on_backup_event(
                CreateBackupEvent(
                    reason=None,
                    stage=CreateBackupStage.CLEANING_UP,
                    state=CreateBackupState.IN_PROGRESS,
                )
            )
            await delete_backups_exceeding_configured_count(self)

        finally:
            self._backup_task = None
            self._backup_finish_task = None
            if backup_success:
                self.async_on_backup_event(
                    CreateBackupEvent(
                        reason=None,
                        stage=None,
                        state=CreateBackupState.COMPLETED,
                    )
                )
            else:
                self.async_on_backup_event(
                    CreateBackupEvent(
                        reason="upload_failed",
                        stage=None,
                        state=CreateBackupState.FAILED,
                    )
                )
            self.async_on_backup_event(IdleEvent())