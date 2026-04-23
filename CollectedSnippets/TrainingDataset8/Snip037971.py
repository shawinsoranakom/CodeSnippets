def remove_orphaned_files(self) -> None:
        """Remove all files that are no longer referenced by any active session.

        Safe to call from any thread.
        """
        LOGGER.debug("Removing orphaned files...")

        with self._lock:
            for file_id in self._get_inactive_file_ids():
                file = self._file_metadata[file_id]
                if file.kind == MediaFileKind.MEDIA:
                    self._delete_file(file_id)
                elif file.kind == MediaFileKind.DOWNLOADABLE:
                    if file.is_marked_for_delete:
                        self._delete_file(file_id)
                    else:
                        file.mark_for_delete()