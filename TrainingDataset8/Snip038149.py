def clear(self) -> None:
        """Reset self completely, clearing all current and old values."""
        self._old_state.clear()
        self._new_session_state.clear()
        self._new_widget_state.clear()
        self._key_id_mapping.clear()