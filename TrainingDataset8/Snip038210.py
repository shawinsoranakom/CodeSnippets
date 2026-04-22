def remove_files(self, session_id: str, widget_id: str) -> None:
        """Remove the file list for the provided widget in the
        provided session, if it exists.

        The "on_files_updated" Signal will be emitted.

        Safe to call from any thread.

        Parameters
        ----------
        session_id : str
            The ID of the session that owns the files.
        widget_id : str
            The widget ID of the FileUploader that created the files.
        """
        self._remove_files(session_id, widget_id)
        self.on_files_updated.send(session_id)