def _on_source_file_changed(self, filepath: Optional[str] = None) -> None:
        """One of our source files changed. Schedule a rerun if appropriate."""
        if filepath is not None and not self._should_rerun_on_file_change(filepath):
            return

        if self._run_on_save:
            self.request_rerun(self._client_state)
        else:
            self._enqueue_forward_msg(self._create_file_change_message())