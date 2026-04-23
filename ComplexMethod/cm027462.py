async def async_delete_backup(
        self,
        backup_id: str,
        **kwargs: Any,
    ) -> None:
        """Delete a backup file.

        :param backup_id: The ID of the backup that was returned in async_list_backups.
        """
        (filename_tar, filename_meta) = await self._async_backup_filenames(backup_id)

        for filename in (filename_tar, filename_meta):
            try:
                await self._file_station.delete_file(path=self.path, filename=filename)
            except SynologyDSMAPIErrorException as err:
                err_args: dict = err.args[0]
                if int(err_args.get("code", 0)) != 900 or (
                    (err_details := err_args.get("details")) is not None
                    and isinstance(err_details, list)
                    and isinstance(err_details[0], dict)
                    and int(err_details[0].get("code", 0))
                    != 408  # No such file or directory
                ):
                    LOGGER.error("Failed to delete backup: %s", err)
                    raise BackupAgentError("Failed to delete backup") from err