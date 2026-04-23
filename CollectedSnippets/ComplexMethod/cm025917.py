async def async_get_backup(self, backup_id: str, **kwargs: Any) -> AgentBackup:
        """Get a specific backup by its ID from Backblaze B2."""
        if self._backup_list_cache and self._is_cache_valid(
            self._backup_list_cache_expiration
        ):
            if backup := self._backup_list_cache.get(backup_id):
                _LOGGER.debug("Returning backup %s from cache", backup_id)
                return backup

        file, metadata_file_version = await self._find_file_and_metadata_version_by_id(
            backup_id
        )
        if not file or not metadata_file_version:
            raise BackupNotFound(f"Backup {backup_id} not found")

        try:
            metadata_content = await asyncio.wait_for(
                self._hass.async_add_executor_job(
                    self._download_and_parse_metadata_sync,
                    metadata_file_version,
                ),
                timeout=METADATA_DOWNLOAD_TIMEOUT,
            )
        except TimeoutError:
            raise BackupAgentError(
                f"Timeout downloading metadata for backup {backup_id}"
            ) from None

        _LOGGER.debug(
            "Successfully retrieved metadata for backup ID %s from file %s",
            backup_id,
            metadata_file_version.file_name,
        )
        backup = _create_backup_from_metadata(metadata_content, file)

        if self._is_cache_valid(self._backup_list_cache_expiration):
            self._backup_list_cache[backup.backup_id] = backup

        return backup