def _remove_files(self, session_id: str, widget_id: str) -> None:
        """Remove the file list for the provided widget in the
        provided session, if it exists.

        Does not emit any signals.

        Safe to call from any thread.
        """
        files_by_widget = session_id, widget_id
        with self._files_lock:
            self._files_by_id.pop(files_by_widget, None)