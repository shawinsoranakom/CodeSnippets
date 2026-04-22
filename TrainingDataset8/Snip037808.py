def __init__(self):
        self._caches_lock = threading.Lock()
        self._function_caches: Dict[str, "MemoCache"] = {}