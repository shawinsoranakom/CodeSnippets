def handle_backmsg(self, session_id: str, msg: BackMsg) -> None:
        """Send a BackMsg to a connected session.

        Parameters
        ----------
        session_id
            The session's unique ID.
        msg
            The BackMsg to deliver to the session.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """
        if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
            raise RuntimeStoppedError(f"Can't handle_backmsg (state={self._state})")

        session_info = self._session_info_by_id.get(session_id)
        if session_info is None:
            LOGGER.debug(
                "Discarding BackMsg for disconnected session (id=%s)", session_id
            )
            return

        session_info.session.handle_backmsg(msg)