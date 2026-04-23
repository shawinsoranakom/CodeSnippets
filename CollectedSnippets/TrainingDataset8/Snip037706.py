def __init__(
        self,
        session_data: SessionData,
        uploaded_file_manager: UploadedFileManager,
        message_enqueued_callback: Optional[Callable[[], None]],
        local_sources_watcher: LocalSourcesWatcher,
        user_info: Dict[str, Optional[str]],
    ):
        """Initialize the AppSession.

        Parameters
        ----------
        session_data : SessionData
            Object storing parameters related to running a script

        uploaded_file_manager : UploadedFileManager
            The server's UploadedFileManager.

        message_enqueued_callback : Callable[[], None]
            After enqueuing a message, this callable notification will be invoked.

        local_sources_watcher: LocalSourcesWatcher
            The file watcher that lets the session know local files have changed.

        user_info: Dict
            A dict that contains information about the current user. For now,
            it only contains the user's email address.

            {
                "email": "example@example.com"
            }

            Information about the current user is optionally provided when a
            websocket connection is initialized via the "X-Streamlit-User" header.

        """
        # Each AppSession has a unique string ID.
        self.id = str(uuid.uuid4())

        self._event_loop = asyncio.get_running_loop()
        self._session_data = session_data
        self._uploaded_file_mgr = uploaded_file_manager
        self._message_enqueued_callback = message_enqueued_callback

        self._state = AppSessionState.APP_NOT_RUNNING

        # Need to remember the client state here because when a script reruns
        # due to the source code changing we need to pass in the previous client state.
        self._client_state = ClientState()

        self._local_sources_watcher = local_sources_watcher
        self._local_sources_watcher.register_file_change_callback(
            self._on_source_file_changed
        )
        self._stop_config_listener = config.on_config_parsed(
            self._on_source_file_changed, force_connect=True
        )
        self._stop_pages_listener = source_util.register_pages_changed_callback(
            self._on_pages_changed
        )

        # The script should rerun when the `secrets.toml` file has been changed.
        secrets_singleton._file_change_listener.connect(self._on_secrets_file_changed)

        self._run_on_save = config.get_option("server.runOnSave")

        self._scriptrunner: Optional[ScriptRunner] = None

        # This needs to be lazily imported to avoid a dependency cycle.
        from streamlit.runtime.state import SessionState

        self._session_state = SessionState()
        self._user_info = user_info

        self._debug_last_backmsg_id: Optional[str] = None

        LOGGER.debug("AppSession initialized (id=%s)", self.id)