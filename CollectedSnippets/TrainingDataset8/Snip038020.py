def is_active_session(self, session_id: str) -> bool:
        """True if the session_id belongs to an active session.

        Notes
        -----
        Threading: SAFE. May be called on any thread.
        """
        # Dictionary membership is atomic in CPython, so this is thread-safe.
        return session_id in self._session_info_by_id