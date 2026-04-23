def _set_state(self, new_state: RuntimeState) -> None:
        LOGGER.debug("Runtime state: %s -> %s", self._state, new_state)
        self._state = new_state