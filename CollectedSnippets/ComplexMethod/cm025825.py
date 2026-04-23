async def _async_create_backup(
        self,
        *,
        agent_ids: list[str],
        backup_id: str,
        backup_name: str,
        date_str: str,
        extra_metadata: dict[str, bool | str],
        include_database: bool,
        on_progress: Callable[[CreateBackupEvent], None],
        password: str | None,
    ) -> WrittenBackup:
        """Generate a backup."""
        manager = self._hass.data[DATA_MANAGER]

        agent_config = manager.config.data.agents.get(self._local_agent_id)
        if (
            self._local_agent_id in agent_ids
            and agent_config
            and not agent_config.protected
        ):
            password = None

        backup = AgentBackup(
            addons=[],
            backup_id=backup_id,
            database_included=include_database,
            date=date_str,
            extra_metadata=extra_metadata,
            folders=[],
            homeassistant_included=True,
            homeassistant_version=HAVERSION,
            name=backup_name,
            protected=password is not None,
            size=0,
        )

        local_agent_tar_file_path = None
        if self._local_agent_id in agent_ids:
            local_agent = manager.local_backup_agents[self._local_agent_id]
            local_agent_tar_file_path = local_agent.get_new_backup_path(backup)

        on_progress(
            CreateBackupEvent(
                reason=None,
                stage=CreateBackupStage.HOME_ASSISTANT,
                state=CreateBackupState.IN_PROGRESS,
            )
        )
        try:
            # Inform integrations a backup is about to be made
            await manager.async_pre_backup_actions()

            backup_data = {
                "compressed": True,
                "date": date_str,
                "extra": extra_metadata,
                "homeassistant": {
                    "exclude_database": not include_database,
                    "version": HAVERSION,
                },
                "name": backup_name,
                "protected": password is not None,
                "slug": backup_id,
                "type": "partial",
                "version": 2,
            }

            tar_file_path, size_in_bytes = await self._hass.async_add_executor_job(
                self._mkdir_and_generate_backup_contents,
                backup_data,
                include_database,
                password,
                local_agent_tar_file_path,
            )
        except (BackupManagerError, OSError, tarfile.TarError, ValueError) as err:
            # BackupManagerError from async_pre_backup_actions
            # OSError from file operations
            # TarError from tarfile
            # ValueError from json_bytes
            raise BackupReaderWriterError(str(err)) from err
        else:
            backup = replace(backup, size=size_in_bytes)

            async_add_executor_job = self._hass.async_add_executor_job

            async def send_backup() -> AsyncIterator[bytes]:
                try:
                    f = await async_add_executor_job(tar_file_path.open, "rb")
                    try:
                        while chunk := await async_add_executor_job(f.read, 2**20):
                            yield chunk
                    finally:
                        await async_add_executor_job(f.close)
                except OSError as err:
                    raise BackupReaderWriterError(str(err)) from err

            async def open_backup() -> AsyncIterator[bytes]:
                return send_backup()

            async def remove_backup() -> None:
                if local_agent_tar_file_path:
                    return
                try:
                    await async_add_executor_job(tar_file_path.unlink, True)
                except OSError as err:
                    raise BackupReaderWriterError(str(err)) from err

            return WrittenBackup(
                addon_errors={},
                backup=backup,
                folder_errors={},
                open_stream=open_backup,
                release_stream=remove_backup,
            )
        finally:
            # Inform integrations the backup is done
            # If there's an unhandled exception, we keep it so we can rethrow it in case
            # the post backup actions also fail.
            unhandled_exc = sys.exception()
            try:
                try:
                    await manager.async_post_backup_actions()
                except BackupManagerError as err:
                    raise BackupReaderWriterError(str(err)) from err
            except Exception as err:
                if not unhandled_exc:
                    raise
                # If there's an unhandled exception, we wrap both that and the exception
                # from the post backup actions in an ExceptionGroup so the caller is
                # aware of both exceptions.
                raise BackupManagerExceptionGroup(
                    f"Multiple errors when creating backup: {unhandled_exc}, {err}",
                    [unhandled_exc, err],
                ) from None