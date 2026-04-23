def close_session(self, session_id: str) -> None:
        """Close a session. It will stop producing ForwardMsgs.

        This function may be called multiple times for the same session,
        which is not an error. (Subsequent calls just no-op.)

        Parameters
        ----------
        session_id
            The session's unique ID.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """
        if session_id in self._session_info_by_id:
            session_info = self._session_info_by_id[session_id]
            del self._session_info_by_id[session_id]
            session_info.session.shutdown()

        if (
            self._state == RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED
            and len(self._session_info_by_id) == 0
        ):
            self._get_async_objs().has_connection.clear()
            self._set_state(RuntimeState.NO_SESSIONS_CONNECTED)