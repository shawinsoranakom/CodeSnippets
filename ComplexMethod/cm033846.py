def __init__(
        self,
        inventory: InventoryManager,
        variable_manager: VariableManager,
        loader: DataLoader,
        passwords: dict[str, str | None],
        stdout_callback_name: str | None = None,
        run_additional_callbacks: bool = True,
        run_tree: bool = False,
        forks: int | None = None,
    ) -> None:
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._stats = AggregateStats()
        self.passwords = passwords
        self._stdout_callback_name: str | None = stdout_callback_name or C.DEFAULT_STDOUT_CALLBACK
        self._run_additional_callbacks = run_additional_callbacks
        self._run_tree = run_tree
        self._forks = forks or 5

        self._callback_plugins: list[CallbackBase] = []
        self._start_at_done = False

        _rpc_host.LocalManager.shared_instance()  # ensure the RPC host is available

        # make sure any module paths (if specified) are added to the module_loader
        if context.CLIARGS.get('module_path', False):
            for path in context.CLIARGS['module_path']:
                if path:
                    module_loader.add_directory(path)

        # a special flag to help us exit cleanly
        self._terminated = False

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts: dict[str, t.Literal[True]] = dict()
        self._unreachable_hosts: dict[str, t.Literal[True]] = dict()

        try:
            self._final_q = FinalQueue()
        except OSError as e:
            raise AnsibleError("Unable to use multiprocessing, this is normally caused by lack of access to /dev/shm: %s" % to_native(e))

        try:
            # Done in tqm, and not display, because this is only needed for commands that execute tasks
            for fd in (STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO):
                os.set_inheritable(fd, False)
        except Exception as ex:
            display.error_as_warning("failed to set stdio as non inheritable", exception=ex)

        self._callback_lock = threading.Lock()

        # A temporary file (opened pre-fork) used by connection
        # plugins for inter-process locking.
        self._connection_lockfile = tempfile.TemporaryFile()

        self._workers: list[WorkerProcess | None] = []

        # signal handlers to propagate signals to workers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)