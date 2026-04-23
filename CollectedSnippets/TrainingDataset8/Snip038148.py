def _compact_state(self) -> None:
        """Copy all current session_state and widget_state values into our
        _old_state dict, and then clear our current session_state and
        widget_state.
        """
        for key_or_wid in self:
            self._old_state[key_or_wid] = self[key_or_wid]
        self._new_session_state.clear()
        self._new_widget_state.clear()