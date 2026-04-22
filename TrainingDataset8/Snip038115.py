def disconnect(self) -> None:
        """Disconnect the wrapper from its underlying SessionState.
        ScriptRunner calls this when it gets a stop request. After this
        function is called, all future SessionState interactions are no-ops.
        """
        with self._lock:
            self._disconnected = True