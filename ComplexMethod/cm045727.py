def get_snapshot_diff(self):
        root_folder = self._context.web.get_folder_by_server_relative_path(
            self._root_path
        )
        files = root_folder.get_files(self._recursive).execute_query_retry()

        updated_entries = []
        deleted_entries = []
        seen_objects = set()

        for file in files:
            metadata = _SharePointEntryMeta(file)
            metadata.update(self.common_metadata)
            size_limit_exceeded = (
                self._object_size_limit is not None
                and metadata.size > self._object_size_limit
            )
            if size_limit_exceeded:
                metadata.status = STATUS_SIZE_LIMIT_EXCEEDED
                logging.info(
                    f"Skipping object {metadata.as_dict()} because its size "
                    f"{metadata.size} exceeds the limit {self._object_size_limit}"
                )
            if self._is_changed(metadata):
                if size_limit_exceeded:
                    content = b""
                else:
                    content = file.get_content().execute_query_retry().value
                updated_entries.append((content, metadata))
                self._stored_metadata[metadata.path] = metadata
            seen_objects.add(metadata.path)

        for path in self._stored_metadata:
            if path not in seen_objects:
                deleted_entries.append(path)

        for path in deleted_entries:
            self._stored_metadata.pop(path)

        return _SharePointUpdate(updated_entries, deleted_entries)