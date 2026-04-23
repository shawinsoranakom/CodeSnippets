def __init__(self, collectors=None, db=..., profile_session=None,
                 description=None, disable_gc=False, params=None, log=False):
        """
        :param db: database name to use to save results.
            Will try to define database automatically by default.
            Use value ``None`` to not save results in a database.
        :param collectors: list of string and Collector object Ex: ['sql', PeriodicCollector(interval=0.2)]. Use `None` for default collectors
        :param profile_session: session description to use to reproup multiple profile. use make_session(name) for default format.
        :param description: description of the current profiler Suggestion: (route name/test method/loading module, ...)
        :param disable_gc: flag to disable gc durring profiling (usefull to avoid gc while profiling, especially during sql execution)
        :param params: parameters usable by collectors (like frame interval)
        """
        self.start_time = 0
        self.duration = 0
        self.start_cpu_time = 0
        self.cpu_duration = 0
        self.profile_session = profile_session or make_session()
        self.description = description
        self.init_frame = None
        self.init_stack_trace = None
        self.init_thread = None
        self.disable_gc = disable_gc
        self.filecache = {}
        self.params = params or {}  # custom parameters usable by collectors
        self.profile_id = None
        self.log = log
        self.sub_profilers = []
        self.entry_count_limit = int(self.params.get("entry_count_limit",0)) # the limit could be set using a smarter way
        self.done = False
        self.exit_stack = ExitStack()
        self.counter = 0

        if db is ...:
            # determine database from current thread
            db = getattr(threading.current_thread(), 'dbname', None)
            if not db:
                # only raise if path is not given and db is not explicitely disabled
                raise Exception('Database name cannot be defined automaticaly. \n Please provide a valid/falsy dbname or path parameter')
        self.db = db

        # collectors
        if collectors is None:
            collectors = ['sql', 'traces_async']
        self.collectors = []
        for collector in collectors:
            if isinstance(collector, str):
                try:
                    collector = Collector.make(collector)
                except Exception:
                    _logger.error("Could not create collector with name %r", collector)
                    continue
            collector.profiler = self
            self.collectors.append(collector)