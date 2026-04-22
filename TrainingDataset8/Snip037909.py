def __init__(self):
        # Contains a cache object for each st.cache'd function
        self._lock = threading.RLock()
        self._function_caches: Dict[str, MemCache] = {}