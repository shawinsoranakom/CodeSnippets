def _yield_files_recursive(
            self,
            folder_id: str,
            start: SecondsSinceUnixEpoch | None,
            end: SecondsSinceUnixEpoch | None,
            relative_folder_path: str = "",
        ) -> GenerateDocumentsOutput:

        if self.box_client is None:
            raise ConnectorMissingCredentialError("Box")

        result = self.box_client.folders.get_folder_items(
            folder_id=folder_id,
            limit=self.batch_size,
            usemarker=self.use_marker
        )

        while True:
            batch: list[Document] = []
            for entry in result.entries:
                if entry.type == 'file' :
                    file = self.box_client.files.get_file_by_id(
                        entry.id
                    )
                    modified_time: SecondsSinceUnixEpoch | None = None
                    raw_time = (
                        getattr(file, "created_at", None)
                        or getattr(file, "content_created_at", None)
                    )

                    if raw_time:
                        modified_time = self._box_datetime_to_epoch_seconds(raw_time)
                        if start is not None and modified_time <= start:
                            continue
                        if end is not None and modified_time > end:
                            continue

                    content_bytes = self.box_client.downloads.download_file(file.id)
                    semantic_identifier = (
                        f"{relative_folder_path} / {file.name}"
                        if relative_folder_path
                        else file.name
                    )

                    batch.append(
                        Document(
                            id=f"box:{file.id}",
                            blob=content_bytes.read(),
                            source=DocumentSource.BOX,
                            semantic_identifier=semantic_identifier,
                            extension=get_file_ext(file.name),
                            doc_updated_at=modified_time,
                            size_bytes=file.size,
                            metadata=file.metadata
                        )
                    )
                elif entry.type == 'folder':
                    child_relative_path = (
                        f"{relative_folder_path} / {entry.name}"
                        if relative_folder_path
                        else entry.name
                    )
                    yield from self._yield_files_recursive(
                        folder_id=entry.id,
                        start=start,
                        end=end,
                        relative_folder_path=child_relative_path
                    )

            if batch:
                yield batch

            if not result.next_marker:
                break

            result = self.box_client.folders.get_folder_items(
                folder_id=folder_id,
                limit=self.batch_size,
                marker=result.next_marker,
                usemarker=True
            )