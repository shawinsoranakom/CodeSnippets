def __init__(self, key: str, display_name: str, allow_widgets: bool = False):
        self.key = key
        self.display_name = display_name
        self._mem_cache: Dict[str, MultiCacheResults] = {}
        self._mem_cache_lock = threading.Lock()
        self.allow_widgets = allow_widgets