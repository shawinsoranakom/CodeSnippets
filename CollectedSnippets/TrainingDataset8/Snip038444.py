def __init__(self, main_script_path: str, command_line: Optional[str]):
        """Create the server. It won't be started yet."""
        _set_tornado_log_levels()

        self._main_script_path = main_script_path

        # Initialize MediaFileStorage and its associated endpoint
        media_file_storage = MemoryMediaFileStorage(MEDIA_ENDPOINT)
        MediaFileHandler.initialize_storage(media_file_storage)

        self._runtime = Runtime(
            RuntimeConfig(
                script_path=main_script_path,
                command_line=command_line,
                media_file_storage=media_file_storage,
            ),
        )

        self._runtime.stats_mgr.register_provider(media_file_storage)