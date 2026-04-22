def filtered_state(self) -> Dict[str, Any]:
        """The combined session and widget state, excluding keyless widgets."""
        with self._lock:
            if self._disconnected:
                return {}

            return self._state.filtered_state