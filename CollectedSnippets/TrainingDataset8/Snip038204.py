def add_file(
        self,
        session_id: str,
        widget_id: str,
        file: UploadedFileRec,
    ) -> UploadedFileRec:
        """Add a file to the FileManager, and return a new UploadedFileRec
        with its ID assigned.

        The "on_files_updated" Signal will be emitted.

        Safe to call from any thread.

        Parameters
        ----------
        session_id
            The ID of the session that owns the file.
        widget_id
            The widget ID of the FileUploader that created the file.
        file
            The file to add.

        Returns
        -------
        UploadedFileRec
            The added file, which has its unique ID assigned.
        """
        files_by_widget = session_id, widget_id

        # Assign the file a unique ID
        file_id = self._get_next_file_id()
        file = UploadedFileRec(
            id=file_id, name=file.name, type=file.type, data=file.data
        )

        with self._files_lock:
            file_list = self._files_by_id.get(files_by_widget, None)
            if file_list is not None:
                file_list.append(file)
            else:
                self._files_by_id[files_by_widget] = [file]

        self.on_files_updated.send(session_id)
        return file