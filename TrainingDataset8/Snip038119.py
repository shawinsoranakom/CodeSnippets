def get_widget_states(self) -> List[WidgetStateProto]:
        """Return a list of serialized widget values for each widget with a value."""
        with self._lock:
            if self._disconnected:
                return []

            return self._state.get_widget_states()