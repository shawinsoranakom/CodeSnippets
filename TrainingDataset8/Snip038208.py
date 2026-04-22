def remove_file(self, session_id: str, widget_id: str, file_id: int) -> bool:
        """Remove the file list with the given ID, if it exists.

        The "on_files_updated" Signal will be emitted.

        Safe to call from any thread.

        Returns
        -------
        bool
            True if the file was removed, or False if no such file exists.
        """
        file_list_id = (session_id, widget_id)
        with self._files_lock:
            file_list = self._files_by_id.get(file_list_id, None)
            if file_list is None:
                return False

            # Remove the file from its list.
            new_file_list = [file for file in file_list if file.id != file_id]
            self._files_by_id[file_list_id] = new_file_list

        self.on_files_updated.send(session_id)
        return True