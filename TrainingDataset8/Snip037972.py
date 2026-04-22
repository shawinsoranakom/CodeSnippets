def _delete_file(self, file_id: str) -> None:
        """Delete the given file from storage, and remove its metadata from
        self._files_by_id.

        Thread safety: callers must hold `self._lock`.
        """
        LOGGER.debug("Deleting File: %s", file_id)
        self._storage.delete_file(file_id)
        del self._file_metadata[file_id]