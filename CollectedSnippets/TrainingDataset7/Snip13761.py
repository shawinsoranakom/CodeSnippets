def __init__(
        self, subsuites, processes, failfast=False, debug_mode=False, buffer=False
    ):
        self.subsuites = subsuites
        self.processes = processes
        self.failfast = failfast
        self.debug_mode = debug_mode
        self.buffer = buffer
        self.initial_settings = None
        self.serialized_contents = None
        self.used_aliases = None
        super().__init__()