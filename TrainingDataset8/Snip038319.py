def __init__(self) -> None:
        super(_FolderEventHandler, self).__init__()
        self._watched_paths: Dict[str, WatchedPath] = {}
        self._lock = threading.Lock()