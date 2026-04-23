def handle_backmsg_deserialization_exception(
        self, session_id: str, exc: BaseException
    ) -> None:
        """Handle an Exception raised during deserialization of a BackMsg.

        Parameters
        ----------
        session_id
            The session's unique ID.
        exc
            The Exception.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """
        if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
            raise RuntimeStoppedError(
                f"Can't handle_backmsg_deserialization_exception (state={self._state})"
            )

        session_info = self._session_info_by_id.get(session_id)
        if session_info is None:
            LOGGER.debug(
                "Discarding BackMsg Exception for disconnected session (id=%s)",
                session_id,
            )
            return

        session_info.session.handle_backmsg_exception(exc)