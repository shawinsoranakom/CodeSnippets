def is_new_state_value(self, user_key: str) -> bool:
        with self._lock:
            if self._disconnected:
                return False

            return self._state.is_new_state_value(user_key)