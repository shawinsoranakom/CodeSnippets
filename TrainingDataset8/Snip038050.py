def on_scriptrunner_yield(self) -> Optional[ScriptRequest]:
        """Called by the ScriptRunner when it's at a yield point.

        If we have no request, return None.

        If we have a RERUN request, return the request and set our internal
        state to CONTINUE.

        If we have a STOP request, return the request and remain stopped.
        """
        if self._state == ScriptRequestType.CONTINUE:
            # We avoid taking a lock in the common case. If a STOP or RERUN
            # request is received between the `if` and `return`, it will be
            # handled at the next `on_scriptrunner_yield`, or when
            # `on_scriptrunner_ready` is called.
            return None

        with self._lock:
            if self._state == ScriptRequestType.RERUN:
                self._state = ScriptRequestType.CONTINUE
                return ScriptRequest(ScriptRequestType.RERUN, self._rerun_data)

            assert self._state == ScriptRequestType.STOP
            return ScriptRequest(ScriptRequestType.STOP)