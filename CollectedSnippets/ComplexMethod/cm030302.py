def __init__(self, max_workers=None, mp_context=None,
                 initializer=None, initargs=(), *, max_tasks_per_child=None):
        """Initializes a new ProcessPoolExecutor instance.

        Args:
            max_workers: The maximum number of processes that can be used to
                execute the given calls. If None or not given then as many
                worker processes will be created as the machine has processors.
            mp_context: A multiprocessing context to launch the workers created
                using the multiprocessing.get_context('start method') API. This
                object should provide SimpleQueue, Queue and Process.
            initializer: A callable used to initialize worker processes.
            initargs: A tuple of arguments to pass to the initializer.
            max_tasks_per_child: The maximum number of tasks a worker process
                can complete before it will exit and be replaced with a fresh
                worker process. The default of None means worker process will
                live as long as the executor. Requires a non-'fork' mp_context
                start method. When given, we default to using 'spawn' if no
                mp_context is supplied.
        """
        _check_system_limits()

        if max_workers is None:
            self._max_workers = os.process_cpu_count() or 1
            if sys.platform == 'win32':
                self._max_workers = min(_MAX_WINDOWS_WORKERS,
                                        self._max_workers)
        else:
            if max_workers <= 0:
                raise ValueError("max_workers must be greater than 0")
            elif (sys.platform == 'win32' and
                max_workers > _MAX_WINDOWS_WORKERS):
                raise ValueError(
                    f"max_workers must be <= {_MAX_WINDOWS_WORKERS}")

            self._max_workers = max_workers

        if mp_context is None:
            if max_tasks_per_child is not None:
                mp_context = mp.get_context("spawn")
            else:
                mp_context = mp.get_context()
        self._mp_context = mp_context

        # https://github.com/python/cpython/issues/90622
        self._safe_to_dynamically_spawn_children = (
                self._mp_context.get_start_method(allow_none=False) != "fork")

        if initializer is not None and not callable(initializer):
            raise TypeError("initializer must be a callable")
        self._initializer = initializer
        self._initargs = initargs

        if max_tasks_per_child is not None:
            if not isinstance(max_tasks_per_child, int):
                raise TypeError("max_tasks_per_child must be an integer")
            elif max_tasks_per_child <= 0:
                raise ValueError("max_tasks_per_child must be >= 1")
            if self._mp_context.get_start_method(allow_none=False) == "fork":
                # https://github.com/python/cpython/issues/90622
                raise ValueError("max_tasks_per_child is incompatible with"
                                 " the 'fork' multiprocessing start method;"
                                 " supply a different mp_context.")
        self._max_tasks_per_child = max_tasks_per_child

        # Management thread
        self._executor_manager_thread = None

        # Map of pids to processes
        self._processes = {}

        # Shutdown is a two-step process.
        self._shutdown_thread = False
        self._shutdown_lock = threading.Lock()
        self._idle_worker_semaphore = threading.Semaphore(0)
        self._broken = False
        self._queue_count = 0
        self._pending_work_items = {}
        self._cancel_pending_futures = False

        # _ThreadWakeup is a communication channel used to interrupt the wait
        # of the main loop of executor_manager_thread from another thread (e.g.
        # when calling executor.submit or executor.shutdown). We do not use the
        # _result_queue to send wakeup signals to the executor_manager_thread
        # as it could result in a deadlock if a worker process dies with the
        # _result_queue write lock still acquired.
        #
        # Care must be taken to only call clear and close from the
        # executor_manager_thread, since _ThreadWakeup.clear() is not protected
        # by a lock.
        self._executor_manager_thread_wakeup = _ThreadWakeup()

        # Create communication channels for the executor
        # Make the call queue slightly larger than the number of processes to
        # prevent the worker processes from idling. But don't make it too big
        # because futures in the call queue cannot be cancelled.
        queue_size = self._max_workers + EXTRA_QUEUED_CALLS
        self._call_queue = _SafeQueue(
            max_size=queue_size, ctx=self._mp_context,
            pending_work_items=self._pending_work_items,
            thread_wakeup=self._executor_manager_thread_wakeup)
        # Killed worker processes can produce spurious "broken pipe"
        # tracebacks in the queue's own worker thread. But we detect killed
        # processes anyway, so silence the tracebacks.
        self._call_queue._ignore_epipe = True
        self._result_queue = mp_context.SimpleQueue()
        self._work_ids = queue.Queue()