async def _async_get_backups(self) -> list[tuple[AgentBackup, str]]:
        """Get backups and their corresponding file names."""
        files = await self._api.list_folder("")

        tar_files = {f.name for f in files if f.name.endswith(".tar")}
        metadata_files = [f for f in files if f.name.endswith(".metadata.json")]

        backups: list[tuple[AgentBackup, str]] = []
        for metadata_file in metadata_files:
            tar_name = metadata_file.name.removesuffix(".metadata.json") + ".tar"
            if tar_name not in tar_files:
                _LOGGER.warning(
                    "Found metadata file '%s' without matching backup file",
                    metadata_file.name,
                )
                continue

            metadata_stream = self._api.download_file(f"/{metadata_file.name}")
            raw = b"".join([chunk async for chunk in metadata_stream])
            try:
                data = json.loads(raw)
                backup = AgentBackup.from_dict(data)
            except (json.JSONDecodeError, ValueError, TypeError, KeyError) as err:
                _LOGGER.warning(
                    "Skipping invalid metadata file '%s': %s",
                    metadata_file.name,
                    err,
                )
                continue
            backups.append((backup, tar_name))

        return backups