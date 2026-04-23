def _collect_files_recursive(
        self,
        path: str,
        start: SecondsSinceUnixEpoch | None,
        end: SecondsSinceUnixEpoch | None,
        all_files: list,
    ) -> None:
        """Recursively collect all files matching time criteria."""
        if self.dropbox_client is None:
            raise ConnectorMissingCredentialError("Dropbox")

        result = self.dropbox_client.files_list_folder(
            path,
            recursive=False,
            include_non_downloadable_files=False,
        )

        while True:
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    modified_time = entry.client_modified
                    if modified_time.tzinfo is None:
                        modified_time = modified_time.replace(tzinfo=timezone.utc)
                    else:
                        modified_time = modified_time.astimezone(timezone.utc)

                    time_as_seconds = modified_time.timestamp()
                    if start is not None and time_as_seconds <= start:
                        continue
                    if end is not None and time_as_seconds > end:
                        continue

                    try:
                        downloaded_file = self._download_file(entry.path_display)
                        all_files.append((entry, downloaded_file))
                    except Exception:
                        logger.exception(f"[Dropbox]: Error downloading file {entry.path_display}")
                        continue

                elif isinstance(entry, FolderMetadata):
                    self._collect_files_recursive(entry.path_lower, start, end, all_files)

            if not result.has_more:
                break

            result = self.dropbox_client.files_list_folder_continue(result.cursor)