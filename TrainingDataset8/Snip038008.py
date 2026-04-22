def __init__(self, config: RuntimeConfig):
        """Create a Runtime instance. It won't be started yet.

        Runtime is *not* thread-safe. Its public methods are generally
        safe to call only on the same thread that its event loop runs on.

        Parameters
        ----------
        config
            Config options.
        """
        if Runtime._instance is not None:
            raise RuntimeError("Runtime instance already exists!")
        Runtime._instance = self

        # Will be created when we start.
        self._async_objs: Optional[AsyncObjects] = None

        # The task that runs our main loop. We need to save a reference
        # to it so that it doesn't get garbage collected while running.
        self._loop_coroutine_task: Optional[asyncio.Task[None]] = None

        self._main_script_path = config.script_path
        self._command_line = config.command_line or ""

        # Mapping of AppSession.id -> SessionInfo.
        self._session_info_by_id: Dict[str, SessionInfo] = {}

        self._state = RuntimeState.INITIAL

        # Initialize managers
        self._message_cache = ForwardMsgCache()
        self._uploaded_file_mgr = UploadedFileManager()
        self._uploaded_file_mgr.on_files_updated.connect(self._on_files_updated)
        self._media_file_mgr = MediaFileManager(storage=config.media_file_storage)

        self._stats_mgr = StatsManager()
        self._stats_mgr.register_provider(get_memo_stats_provider())
        self._stats_mgr.register_provider(get_singleton_stats_provider())
        self._stats_mgr.register_provider(_mem_caches)
        self._stats_mgr.register_provider(self._message_cache)
        self._stats_mgr.register_provider(self._uploaded_file_mgr)
        self._stats_mgr.register_provider(
            SessionStateStatProvider(self._session_info_by_id)
        )