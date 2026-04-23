def _get_inactive_file_ids(self) -> Set[str]:
        """Compute the set of files that are stored in the manager, but are
        not referenced by any active session. These are files that can be
        safely deleted.

        Thread safety: callers must hold `self._lock`.
        """
        # Get the set of all our file IDs.
        file_ids = set(self._file_metadata.keys())

        # Subtract all IDs that are in use by each session
        for session_file_ids_by_coord in self._files_by_session_and_coord.values():
            file_ids.difference_update(session_file_ids_by_coord.values())

        return file_ids