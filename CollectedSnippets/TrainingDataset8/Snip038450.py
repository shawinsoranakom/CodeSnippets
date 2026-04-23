def browser_is_connected(self) -> bool:
        return self._runtime.state == RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED