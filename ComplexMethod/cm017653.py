def __init__(
        self,
        pattern=None,
        top_level=None,
        verbosity=1,
        interactive=True,
        failfast=False,
        keepdb=False,
        reverse=False,
        debug_mode=False,
        debug_sql=False,
        parallel=0,
        tags=None,
        exclude_tags=None,
        test_name_patterns=None,
        pdb=False,
        buffer=False,
        enable_faulthandler=True,
        timing=False,
        shuffle=False,
        logger=None,
        durations=None,
        **kwargs,
    ):
        self.pattern = pattern
        self.top_level = top_level
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.keepdb = keepdb
        self.reverse = reverse
        self.debug_mode = debug_mode
        self.debug_sql = debug_sql
        self.parallel = parallel
        self.tags = set(tags or [])
        self.exclude_tags = set(exclude_tags or [])
        if not faulthandler.is_enabled() and enable_faulthandler:
            try:
                faulthandler.enable(file=sys.stderr.fileno())
            except (AttributeError, io.UnsupportedOperation):
                faulthandler.enable(file=sys.__stderr__.fileno())
        self.pdb = pdb
        if self.pdb and self.parallel > 1:
            raise ValueError(
                "You cannot use --pdb with parallel tests; pass --parallel=1 to use it."
            )
        self.buffer = buffer
        self.test_name_patterns = None
        self.time_keeper = TimeKeeper() if timing else NullTimeKeeper()
        if test_name_patterns:
            # unittest does not export the _convert_select_pattern function
            # that converts command-line arguments to patterns.
            self.test_name_patterns = {
                pattern if "*" in pattern else "*%s*" % pattern
                for pattern in test_name_patterns
            }
        self.shuffle = shuffle
        self._shuffler = None
        self.logger = logger
        self.durations = durations