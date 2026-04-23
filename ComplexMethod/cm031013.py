def __init__(self, ns: Namespace, _add_python_opts: bool = False):
        # Log verbosity
        self.verbose: int = int(ns.verbose)
        self.quiet: bool = ns.quiet
        self.pgo: bool = ns.pgo
        self.pgo_extended: bool = ns.pgo_extended
        self.tsan: bool = ns.tsan
        self.tsan_parallel: bool = ns.tsan_parallel

        # Test results
        self.results: TestResults = TestResults()
        self.first_state: str | None = None

        # Logger
        self.logger = Logger(self.results, self.quiet, self.pgo)

        # Actions
        self.want_header: bool = ns.header
        self.want_list_tests: bool = ns.list_tests
        self.want_list_cases: bool = ns.list_cases
        self.want_wait: bool = ns.wait
        self.want_cleanup: bool = ns.cleanup
        self.want_rerun: bool = ns.rerun
        self.want_run_leaks: bool = ns.runleaks
        self.want_bisect: bool = ns.bisect

        self.ci_mode: bool = (ns.fast_ci or ns.slow_ci)
        self.want_add_python_opts: bool = (_add_python_opts
                                           and ns._add_python_opts)

        # Select tests
        self.match_tests: TestFilter = ns.match_tests
        self.exclude: bool = ns.exclude
        self.fromfile: StrPath | None = ns.fromfile
        self.starting_test: TestName | None = ns.start
        self.cmdline_args: TestList = ns.args

        # Workers
        self.single_process: bool = ns.single_process
        if self.single_process or ns.use_mp is None:
            num_workers = 0   # run sequentially in a single process
        elif ns.use_mp <= 0:
            num_workers = -1  # run in parallel, use the number of CPUs
        else:
            num_workers = ns.use_mp  # run in parallel
        self.num_workers: int = num_workers
        self.worker_json: StrJSON | None = ns.worker_json

        # Options to run tests
        self.fail_fast: bool = ns.failfast
        self.fail_env_changed: bool = ns.fail_env_changed
        self.fail_rerun: bool = ns.fail_rerun
        self.forever: bool = ns.forever
        self.output_on_failure: bool = ns.verbose3
        self.timeout: float | None = ns.timeout
        if ns.huntrleaks:
            warmups, runs, filename = ns.huntrleaks
            filename = os.path.abspath(filename)
            self.hunt_refleak: HuntRefleak | None = HuntRefleak(warmups, runs, filename)
        else:
            self.hunt_refleak = None
        self.test_dir: StrPath | None = ns.testdir
        self.junit_filename: StrPath | None = ns.xmlpath
        self.memory_limit: str | None = ns.memlimit
        self.gc_threshold: int | None = ns.threshold
        self.use_resources: dict[str, str | None] = dict(ns.use_resources)
        if ns.python:
            self.python_cmd: tuple[str, ...] | None = tuple(ns.python)
        else:
            self.python_cmd = None
        self.coverage: bool = ns.trace
        self.coverage_dir: StrPath | None = ns.coverdir
        self._tmp_dir: StrPath | None = ns.tempdir
        self.pythoninfo: bool = ns.pythoninfo

        # Randomize
        self.randomize: bool = ns.randomize
        if ('SOURCE_DATE_EPOCH' in os.environ
            # don't use the variable if empty
            and os.environ['SOURCE_DATE_EPOCH']
        ):
            self.randomize = False
            # SOURCE_DATE_EPOCH should be an integer, but use a string to not
            # fail if it's not integer. random.seed() accepts a string.
            # https://reproducible-builds.org/docs/source-date-epoch/
            self.random_seed: int | str = os.environ['SOURCE_DATE_EPOCH']
        elif ns.random_seed is None:
            self.random_seed = random.getrandbits(32)
        else:
            self.random_seed = ns.random_seed
        self.prioritize_tests: tuple[str, ...] = tuple(ns.prioritize)

        self.parallel_threads = ns.parallel_threads

        # tests
        self.first_runtests: RunTests | None = None

        # used by --slowest
        self.print_slowest: bool = ns.print_slow

        # used to display the progress bar "[ 3/100]"
        self.start_time = time.perf_counter()

        # used by --single
        self.single_test_run: bool = ns.single
        self.next_single_test: TestName | None = None
        self.next_single_filename: StrPath | None = None