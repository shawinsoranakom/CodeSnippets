def __init__(self) -> None:
        """Constructor."""
        _MultiPathWatcher._singleton = self

        # Map of folder_to_watch -> _FolderEventHandler.
        self._folder_handlers: Dict[str, _FolderEventHandler] = {}

        # Used for mutation of _folder_handlers dict
        self._lock = threading.Lock()

        # The Observer object from the Watchdog module. Since this class is
        # only instantiated once, we only have a single Observer in Streamlit,
        # and it's in charge of watching all paths we're interested in.
        self._observer = Observer()
        self._observer.start()