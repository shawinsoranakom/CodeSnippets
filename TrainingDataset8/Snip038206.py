def get_files(
        self, session_id: str, widget_id: str, file_ids: List[int]
    ) -> List[UploadedFileRec]:
        """Return the files with the given widget_id and file_ids.

        Safe to call from any thread.

        Parameters
        ----------
        session_id
            The ID of the session that owns the files.
        widget_id
            The widget ID of the FileUploader that created the files.
        file_ids
            List of file IDs. Only files whose IDs are in this list will be
            returned.
        """
        return [
            f for f in self.get_all_files(session_id, widget_id) if f.id in file_ids
        ]