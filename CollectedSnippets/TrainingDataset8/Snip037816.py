def __init__(
        self,
        key: str,
        persist: Optional[str],
        max_entries: float,
        ttl: float,
        display_name: str,
        allow_widgets: bool = False,
    ):
        self.key = key
        self.display_name = display_name
        self.persist = persist
        self._mem_cache: TTLCache[str, bytes] = TTLCache(
            maxsize=max_entries, ttl=ttl, timer=_TTLCACHE_TIMER
        )
        self._mem_cache_lock = threading.Lock()
        self.allow_widgets = allow_widgets