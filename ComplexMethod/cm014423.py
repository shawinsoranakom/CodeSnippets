def __init__(self, loader) -> None:
        super().__init__(loader)

        self._prefetch_factor = loader.prefetch_factor
        self._in_order = loader.in_order

        if self._num_workers <= 0:
            raise AssertionError(
                "num_workers must be greater than 0 for MultiProcessingDataLoaderIter"
            )
        if self._prefetch_factor <= 0:
            raise AssertionError(
                "prefetch_factor must be greater than 0 for MultiProcessingDataLoaderIter"
            )

        if loader.multiprocessing_context is None:
            multiprocessing_context = torch.multiprocessing
        else:
            multiprocessing_context = loader.multiprocessing_context

        self._worker_init_fn = loader.worker_init_fn

        # Adds forward compatibilities so classic DataLoader can work with DataPipes:
        #   Additional worker init function will take care of sharding in MP and Distributed
        if isinstance(self._dataset, (IterDataPipe, MapDataPipe)):
            self._worker_init_fn = functools.partial(
                _sharding_worker_init_fn,
                self._worker_init_fn,
                self._world_size,
                self._rank,
            )

        # No certainty which module multiprocessing_context is
        self._worker_result_queue = multiprocessing_context.Queue()  # type: ignore[var-annotated]
        self._worker_pids_set = False
        self._shutdown = False
        self._workers_done_event = multiprocessing_context.Event()

        self._index_queues = []
        self._workers = []
        for i in range(self._num_workers):
            # No certainty which module multiprocessing_context is
            index_queue = multiprocessing_context.Queue()  # type: ignore[var-annotated]
            # Need to `cancel_join_thread` here!
            # See sections (2) and (3b) above.
            index_queue.cancel_join_thread()
            w = multiprocessing_context.Process(
                target=_utils.worker._worker_loop,
                args=(
                    self._dataset_kind,
                    self._dataset,
                    index_queue,
                    self._worker_result_queue,
                    self._workers_done_event,
                    self._auto_collation,
                    self._collate_fn,
                    self._drop_last,
                    self._base_seed,
                    self._worker_init_fn,
                    i,
                    self._num_workers,
                    self._persistent_workers,
                    self._shared_seed,
                ),
            )
            w.daemon = True
            # NB: Process.start() actually take some time as it needs to
            #     start a process and pass the arguments over via a pipe.
            #     Therefore, we only add a worker to self._workers list after
            #     it started, so that we do not call .join() if program dies
            #     before it starts, and __del__ tries to join but will get:
            #     AssertionError: can only join a started process.
            from pickle import PicklingError

            try:
                w.start()
            except (TypeError, AttributeError, PicklingError):
                warnings.warn(
                    "Got pickle error when attempting to start a worker Process. "
                    "This might be because the worker Process arguments are not picklable. "
                    "Python 3.14+ changed the multiprocessing start method in non-Mac POSIX platforms "
                    "to 'forkserver', which requires the worker Process arguments to be picklable. "
                    "You can also try multiprocessing.set_start_method('fork').",
                    stacklevel=2,
                )
                raise
            self._index_queues.append(index_queue)
            self._workers.append(w)

        if self._pin_memory:
            self._pin_memory_thread_done_event = threading.Event()

            # Queue is not type-annotated
            self._data_queue = queue.Queue()  # type: ignore[var-annotated]
            current_device_id = torch.accelerator.current_device_index()
            pin_memory_thread = threading.Thread(
                target=_utils.pin_memory._pin_memory_loop,
                args=(
                    self._worker_result_queue,
                    self._data_queue,
                    current_device_id,
                    self._pin_memory_thread_done_event,
                    self._pin_memory_device,
                ),
            )
            pin_memory_thread.daemon = True
            pin_memory_thread.start()
            # Similar to workers (see comment above), we only register
            # pin_memory_thread once it is started.
            self._pin_memory_thread = pin_memory_thread
        else:
            self._data_queue = self._worker_result_queue  # type: ignore[assignment]

        # In some rare cases, persistent workers (daemonic processes)
        # would be terminated before `__del__` of iterator is invoked
        # when main process exits
        # It would cause failure when pin_memory_thread tries to read
        # corrupted data from worker_result_queue
        # atexit is used to shutdown thread and child processes in the
        # right sequence before main process exits
        if self._persistent_workers and self._pin_memory:
            import atexit

            for w in self._workers:
                atexit.register(_MultiProcessingDataLoaderIter._clean_up_worker, w)

        # .pid can be None only before process is spawned (not the case, so ignore)
        _utils.signal_handling._set_worker_pids(
            id(self),
            tuple(w.pid for w in self._workers),  # type: ignore[misc]
        )
        _utils.signal_handling._set_SIGCHLD_handler()
        self._worker_pids_set = True
        self._reset(loader, first_iter=True)