def get_all_files(self, session_id: str, widget_id: str) -> List[UploadedFileRec]:
        """Return all the files stored for the given widget.

        Safe to call from any thread.

        Parameters
        ----------
        session_id
            The ID of the session that owns the files.
        widget_id
            The widget ID of the FileUploader that created the files.
        """
        file_list_id = (session_id, widget_id)
        with self._files_lock:
            return self._files_by_id.get(file_list_id, []).copy()