def _on_files_updated(self, session_id: str) -> None:
        """Event handler for UploadedFileManager.on_file_added.
        Ensures that uploaded files from stale sessions get deleted.

        Notes
        -----
        Threading: SAFE. May be called on any thread.
        """
        session_info = self._get_session_info(session_id)
        if session_info is None:
            # If an uploaded file doesn't belong to an existing session,
            # remove it so it doesn't stick around forever.
            self._uploaded_file_mgr.remove_session_files(session_id)