def _set_execing_flag(self):
        """A context for setting the ScriptRunner._execing flag.

        Used by _maybe_handle_execution_control_request to ensure that
        we only handle requests while we're inside an exec() call
        """
        if self._execing:
            raise RuntimeError("Nested set_execing_flag call")
        self._execing = True
        try:
            yield
        finally:
            self._execing = False