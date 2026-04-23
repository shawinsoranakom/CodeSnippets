def __init__(self, file_path: str):
        # Our secrets dict.
        self._secrets: Optional[Mapping[str, Any]] = None
        self._lock = threading.RLock()
        self._file_watcher_installed = False
        self._file_path = file_path
        self._file_change_listener = Signal(
            doc="Emitted when the `secrets.toml` file has been changed."
        )