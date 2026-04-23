def create_session(
        self,
        client: SessionClient,
        user_info: Dict[str, Optional[str]],
    ) -> str:
        """Create a new session and return its unique ID.

        Parameters
        ----------
        client
            A concrete SessionClient implementation for communicating with
            the session's client.
        user_info
            A dict that contains information about the session's user. For now,
            it only (optionally) contains the user's email address.

            {
                "email": "example@example.com"
            }

        Returns
        -------
        str
            The session's unique string ID.

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """
        if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
            raise RuntimeStoppedError(f"Can't create_session (state={self._state})")

        async_objs = self._get_async_objs()

        session = AppSession(
            session_data=SessionData(self._main_script_path, self._command_line or ""),
            uploaded_file_manager=self._uploaded_file_mgr,
            message_enqueued_callback=self._enqueued_some_message,
            local_sources_watcher=LocalSourcesWatcher(self._main_script_path),
            user_info=user_info,
        )

        LOGGER.debug(
            "Created new session for client %s. Session ID: %s", id(client), session.id
        )

        assert (
            session.id not in self._session_info_by_id
        ), f"session.id '{session.id}' registered multiple times!"

        self._session_info_by_id[session.id] = SessionInfo(client, session)
        self._set_state(RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED)
        async_objs.has_connection.set()

        return session.id