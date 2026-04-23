async def _list_cached_metadata_files(self) -> dict[str, AgentBackup]:
        """List metadata files with a cache."""
        if time() <= self._cache_expiration:
            return self._cache_backup_metadata

        async def _download_metadata(item_id: str) -> AgentBackup | None:
            """Download metadata file."""
            try:
                metadata_stream = await self._client.download_drive_item(item_id)
            except OneDriveException as err:
                _LOGGER.warning("Error downloading metadata for %s: %s", item_id, err)
                return None

            return AgentBackup.from_dict(
                json_loads_object(await metadata_stream.read())
            )

        items = await self._client.list_drive_items(self._folder_id)

        # Build a set of backup filenames to check for orphaned metadata
        backup_filenames = {
            item.name for item in items if item.name and item.name.endswith(".tar")
        }

        metadata_files: dict[str, AgentBackup] = {}
        for item in items:
            if item.name and item.name.endswith(".metadata.json"):
                # Check if corresponding backup file exists
                backup_filename = f"{item.name[: -len('.metadata.json')]}.tar"
                if backup_filename not in backup_filenames:
                    _LOGGER.warning(
                        "Backup file %s not found for metadata %s",
                        backup_filename,
                        item.name,
                    )
                    continue
                if metadata := await _download_metadata(item.id):
                    metadata_files[metadata.backup_id] = metadata

        self._cache_backup_metadata = metadata_files
        self._cache_expiration = time() + CACHE_TTL
        return self._cache_backup_metadata