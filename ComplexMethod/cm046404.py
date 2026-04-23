def __init__(self) -> None:
        """Initialize the Events instance with queue, rate limiter, and environment metadata."""
        self.events = []  # pending events
        self.rate_limit = 30.0  # rate limit (seconds)
        self.t = 0.0  # last send timestamp (seconds)
        self.metadata = {
            "cli": Path(ARGV[0]).name == "yolo",
            "install": "git" if GIT.is_repo else "pip" if IS_PIP_PACKAGE else "other",
            "python": PYTHON_VERSION.rsplit(".", 1)[0],  # i.e. 3.13
            "CPU": get_cpu_info(),
            # "GPU": get_gpu_info(index=0) if cuda else None,
            "version": __version__,
            "env": ENVIRONMENT,
            "session_id": round(random.random() * 1e15),
            "engagement_time_msec": 1000,
        }
        self.enabled = (
            SETTINGS["sync"]
            and RANK in {-1, 0}
            and not TESTS_RUNNING
            and ONLINE
            and (IS_PIP_PACKAGE or GIT.origin == "https://github.com/ultralytics/ultralytics.git")
        )