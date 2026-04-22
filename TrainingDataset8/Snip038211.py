def remove_session_files(self, session_id: str) -> None:
        """Remove all files that belong to the given session.

        Safe to call from any thread.

        Parameters
        ----------
        session_id : str
            The ID of the session whose files we're removing.

        """
        # Copy the keys into a list, because we'll be mutating the dictionary.
        with self._files_lock:
            all_ids = list(self._files_by_id.keys())

        for files_id in all_ids:
            if files_id[0] == session_id:
                self.remove_files(*files_id)