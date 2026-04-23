def __init__(self):
        self.roots = defaultdict(set)
        self.processed_request = threading.Event()
        self.client_timeout = int(os.environ.get("DJANGO_WATCHMAN_TIMEOUT", 5))
        super().__init__()