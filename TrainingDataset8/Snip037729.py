def _handle_stop_script_request(self) -> None:
        """Tell the ScriptRunner to stop running its script."""
        if self._scriptrunner is not None:
            self._scriptrunner.request_stop()