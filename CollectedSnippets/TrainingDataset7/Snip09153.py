def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS):
        # Connection related attributes.
        # The underlying database connection.
        self.connection = None
        # `settings_dict` should be a dictionary containing keys such as
        # NAME, USER, etc. It's called `settings_dict` instead of `settings`
        # to disambiguate it from Django settings modules.
        self.settings_dict = settings_dict
        self.alias = alias
        # Query logging in debug mode or when explicitly enabled.
        self.queries_log = deque(maxlen=self.queries_limit)
        self.force_debug_cursor = False

        # Transaction related attributes.
        # Tracks if the connection is in autocommit mode. Per PEP 249, by
        # default, it isn't.
        self.autocommit = False
        # Tracks if the connection is in a transaction managed by 'atomic'.
        self.in_atomic_block = False
        # Increment to generate unique savepoint ids.
        self.savepoint_state = 0
        # List of savepoints created by 'atomic'.
        self.savepoint_ids = []
        # Stack of active 'atomic' blocks.
        self.atomic_blocks = []
        # Tracks if the outermost 'atomic' block should commit on exit,
        # ie. if autocommit was active on entry.
        self.commit_on_exit = True
        # Tracks if the transaction should be rolled back to the next
        # available savepoint because of an exception in an inner block.
        self.needs_rollback = False
        self.rollback_exc = None

        # Connection termination related attributes.
        self.close_at = None
        self.closed_in_transaction = False
        self.errors_occurred = False
        self.health_check_enabled = False
        self.health_check_done = False

        # Thread-safety related attributes.
        self._thread_sharing_lock = threading.Lock()
        self._thread_sharing_count = 0
        self._thread_ident = _thread.get_ident()

        # A list of no-argument functions to run when the transaction commits.
        # Each entry is an (sids, func, robust) tuple, where sids is a set of
        # the active savepoint IDs when this function was registered and robust
        # specifies whether it's allowed for the function to fail.
        self.run_on_commit = []

        # Should we run the on-commit hooks the next time set_autocommit(True)
        # is called?
        self.run_commit_hooks_on_set_autocommit_on = False

        # A stack of wrappers to be invoked around execute()/executemany()
        # calls. Each entry is a function taking five arguments: execute, sql,
        # params, many, and context. It's the function's responsibility to
        # call execute(sql, params, many, context).
        self.execute_wrappers = []

        self.client = self.client_class(self)
        self.creation = self.creation_class(self)
        self.features = self.features_class(self)
        self.introspection = self.introspection_class(self)
        self.ops = self.ops_class(self)
        self.validation = self.validation_class(self)