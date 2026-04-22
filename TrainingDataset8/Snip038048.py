def request_stop(self) -> None:
        """Request that the ScriptRunner stop running. A stopped ScriptRunner
        can't be used anymore. STOP requests succeed unconditionally.
        """
        with self._lock:
            self._state = ScriptRequestType.STOP