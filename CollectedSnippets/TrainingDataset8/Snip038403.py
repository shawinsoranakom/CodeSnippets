def on_close(self) -> None:
        if not self._session_id:
            return
        self._runtime.close_session(self._session_id)
        self._session_id = None