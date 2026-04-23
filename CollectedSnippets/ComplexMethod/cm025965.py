async def _async_wait_for_backup(
        self,
        backup: supervisor_backups.NewBackup,
        locations: list[str],
        *,
        on_progress: Callable[[CreateBackupEvent], None],
        remove_after_upload: bool,
    ) -> WrittenBackup:
        """Wait for a backup to complete."""
        backup_complete = asyncio.Event()
        backup_id: str | None = None
        create_errors: list[dict[str, str]] = []

        @callback
        def on_job_progress(data: Mapping[str, Any]) -> None:
            """Handle backup progress."""
            nonlocal backup_id
            if not (stage := try_parse_enum(CreateBackupStage, data.get("stage"))):
                _LOGGER.debug("Unknown create stage: %s", data.get("stage"))
            else:
                on_progress(
                    CreateBackupEvent(
                        reason=None, stage=stage, state=CreateBackupState.IN_PROGRESS
                    )
                )
            if data.get("done") is True:
                backup_id = data.get("reference")
                create_errors.extend(data.get("errors", []))
                backup_complete.set()

        unsub = self._async_listen_job_events(backup.job_id, on_job_progress)
        try:
            await self._get_job_state(backup.job_id, on_job_progress)
            await backup_complete.wait()
        finally:
            unsub()
        if not backup_id or create_errors:
            # We should add more specific error handling here in the future
            raise BackupReaderWriterError(
                f"Backup failed: {create_errors or 'no backup_id'}"
            )

        # The backup was created successfully, check for non critical errors
        full_status = await self._client.jobs.get_job(backup.job_id)
        _addon_errors = _collect_errors(
            full_status, "backup_store_addons", "backup_addon_save"
        )
        addon_errors: dict[str, AddonErrorData] = {}
        for slug, errors in _addon_errors.items():
            try:
                addon_info = await self._client.addons.addon_info(slug)
                addon_errors[slug] = AddonErrorData(
                    addon=AddonInfo(
                        name=addon_info.name,
                        slug=addon_info.slug,
                        version=addon_info.version,
                    ),
                    errors=errors,
                )
            except SupervisorError as err:
                _LOGGER.debug("Error getting addon %s: %s", slug, err)
                addon_errors[slug] = AddonErrorData(
                    addon=AddonInfo(name=None, slug=slug, version=None), errors=errors
                )

        _folder_errors = _collect_errors(
            full_status, "backup_store_folders", "backup_folder_save"
        )
        folder_errors = {Folder(key): val for key, val in _folder_errors.items()}

        async def open_backup() -> AsyncIterator[bytes]:
            try:
                return await self._client.backups.download_backup(backup_id)
            except SupervisorError as err:
                raise BackupReaderWriterError(
                    f"Error downloading backup: {err}"
                ) from err

        async def remove_backup() -> None:
            if not remove_after_upload:
                return
            try:
                await self._client.backups.remove_backup(
                    backup_id,
                    options=supervisor_backups.RemoveBackupOptions(
                        location={LOCATION_CLOUD_BACKUP}
                    ),
                )
            except SupervisorError as err:
                raise BackupReaderWriterError(f"Error removing backup: {err}") from err

        try:
            details = await self._client.backups.backup_info(backup_id)
        except SupervisorError as err:
            raise BackupReaderWriterError(
                f"Error getting backup details: {err}"
            ) from err

        return WrittenBackup(
            addon_errors=addon_errors,
            backup=_backup_details_to_agent_backup(details, locations[0]),
            folder_errors=folder_errors,
            open_stream=open_backup,
            release_stream=remove_backup,
        )