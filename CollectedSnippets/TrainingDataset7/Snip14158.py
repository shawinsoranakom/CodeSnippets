def __init__(self):
        self.extra_files = set()
        self.directory_globs = defaultdict(set)
        self._stop_condition = threading.Event()