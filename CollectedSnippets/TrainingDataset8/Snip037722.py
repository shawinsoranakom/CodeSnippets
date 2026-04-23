def _create_session_state_changed_message(self) -> ForwardMsg:
        """Create and return a session_state_changed ForwardMsg."""
        msg = ForwardMsg()
        msg.session_state_changed.run_on_save = self._run_on_save
        msg.session_state_changed.script_is_running = (
            self._state == AppSessionState.APP_IS_RUNNING
        )
        return msg