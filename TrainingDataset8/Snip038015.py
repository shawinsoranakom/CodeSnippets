def get_client(self, session_id: str) -> Optional[SessionClient]:
        """Get the SessionClient for the given session_id, or None
        if no such session exists.

        Notes
        -----
        Threading: SAFE. May be called on any thread.
        """
        session_info = self._get_session_info(session_id)
        if session_info is None:
            return None
        return session_info.client