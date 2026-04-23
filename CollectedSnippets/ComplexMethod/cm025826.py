async def async_restore_backup(
        self,
        backup_id: str,
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        *,
        agent_id: str,
        on_progress: Callable[[RestoreBackupEvent], None],
        password: str | None,
        restore_addons: list[str] | None,
        restore_database: bool,
        restore_folders: list[Folder] | None,
        restore_homeassistant: bool,
    ) -> None:
        """Restore a backup.

        This will write the restore information to .HA_RESTORE which
        will be handled during startup by the restore_backup module.
        """

        if restore_addons or restore_folders:
            raise BackupReaderWriterError(
                "Addons and folders are not supported in core restore"
            )
        if not restore_homeassistant and not restore_database:
            raise BackupReaderWriterError(
                "Home Assistant or database must be included in restore"
            )

        manager = self._hass.data[DATA_MANAGER]
        if agent_id in manager.local_backup_agents:
            local_agent = manager.local_backup_agents[agent_id]
            path = local_agent.get_backup_path(backup_id)
            remove_after_restore = False
        else:
            async_add_executor_job = self._hass.async_add_executor_job
            path = self.temp_backup_dir / f"{backup_id}.tar"
            stream = await open_stream()
            await async_add_executor_job(make_backup_dir, self.temp_backup_dir)
            f = await async_add_executor_job(path.open, "wb")
            try:
                async for chunk in stream:
                    await async_add_executor_job(f.write, chunk)
            finally:
                await async_add_executor_job(f.close)

            remove_after_restore = True

        password_valid = await self._hass.async_add_executor_job(
            validate_password, path, password
        )
        if not password_valid:
            raise IncorrectPasswordError

        def _write_restore_file() -> None:
            """Write the restore file."""
            Path(self._hass.config.path(RESTORE_BACKUP_FILE)).write_text(
                json.dumps(
                    {
                        "path": path.as_posix(),
                        "password": password,
                        "remove_after_restore": remove_after_restore,
                        "restore_database": restore_database,
                        "restore_homeassistant": restore_homeassistant,
                    }
                ),
                encoding="utf-8",
            )

        await self._hass.async_add_executor_job(_write_restore_file)
        on_progress(
            RestoreBackupEvent(
                reason=None,
                stage=None,
                state=RestoreBackupState.CORE_RESTART,
            )
        )
        await self._hass.services.async_call("homeassistant", "restart", blocking=True)