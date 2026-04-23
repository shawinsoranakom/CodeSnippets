def _handle_set_run_on_save_request(self, new_value: bool) -> None:
        """Change our run_on_save flag to the given value.

        The browser will be notified of the change.

        Parameters
        ----------
        new_value : bool
            New run_on_save value

        """
        self._run_on_save = new_value
        self._enqueue_forward_msg(self._create_session_state_changed_message())