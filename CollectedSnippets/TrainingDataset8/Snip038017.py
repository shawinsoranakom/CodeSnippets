def _get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Return the SessionInfo with the given id, or None if no such
        session exists.

        Notes
        -----
        Threading: SAFE. May be called on any thread. (But note that SessionInfo
        mutations are not thread-safe!)
        """
        return self._session_info_by_id.get(session_id, None)