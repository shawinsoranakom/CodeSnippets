def _yield_files_recursive(
        self,
        path: str,
        start: SecondsSinceUnixEpoch | None,
        end: SecondsSinceUnixEpoch | None,
    ) -> GenerateDocumentsOutput:
        """Yield files in batches from a specified Dropbox folder, including subfolders."""
        if self.dropbox_client is None:
            raise ConnectorMissingCredentialError("Dropbox")

        # Collect all files first to count filename occurrences
        all_files = []
        self._collect_files_recursive(path, start, end, all_files)

        # Count filename occurrences
        filename_counts: dict[str, int] = {}
        for entry, _ in all_files:
            filename_counts[entry.name] = filename_counts.get(entry.name, 0) + 1

        # Process files in batches
        batch: list[Document] = []
        for entry, downloaded_file in all_files:
            modified_time = entry.client_modified
            if modified_time.tzinfo is None:
                modified_time = modified_time.replace(tzinfo=timezone.utc)
            else:
                modified_time = modified_time.astimezone(timezone.utc)

            # Use full path only if filename appears multiple times
            if filename_counts.get(entry.name, 0) > 1:
                # Remove leading slash and replace slashes with ' / '
                relative_path = entry.path_display.lstrip('/')
                semantic_id = relative_path.replace('/', ' / ') if relative_path else entry.name
            else:
                semantic_id = entry.name

            batch.append(
                Document(
                    id=f"dropbox:{entry.id}",
                    blob=downloaded_file,
                    source=DocumentSource.DROPBOX,
                    semantic_identifier=semantic_id,
                    extension=get_file_ext(entry.name),
                    doc_updated_at=modified_time,
                    size_bytes=entry.size if getattr(entry, "size", None) is not None else len(downloaded_file),
                )
            )

            if len(batch) == self.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch