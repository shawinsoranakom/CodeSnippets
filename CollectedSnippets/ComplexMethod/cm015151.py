def _test_proper_exit(
    is_iterable_dataset,
    use_workers,
    pin_memory,
    exit_method,
    hold_iter_reference,
    loader_setup_event,
    tester_setup_event,
    persistent_workers,
):
    num_workers = 2 if use_workers else 0

    if exit_method == "worker_error" or exit_method == "worker_kill":
        if use_workers is not True:
            raise AssertionError("Expected use_workers=True for worker exit methods")

    if exit_method == "worker_error":
        worker_error_event = mp.Event()
    else:
        worker_error_event = None

    if is_iterable_dataset:
        ds = TestProperExitIterableDataset(7, worker_error_event)
    else:
        ds = TestProperExitDataset(12, worker_error_event)

    loader = DataLoader(
        ds,
        batch_size=1,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        worker_init_fn=set_faulthander_if_available,
        persistent_workers=persistent_workers,
    )

    error_it = 2

    if use_workers:
        # 2 is the magical per-worker prefetch number...
        # FIXME: change this after the number becomes configurable.
        if is_iterable_dataset:
            if len(ds) * num_workers <= (error_it + 2 + 1):
                raise AssertionError(
                    "Expected iterable dataset size to exceed error threshold"
                )
        else:
            if len(loader) <= (error_it + 2 + 1) * num_workers:
                raise AssertionError("Expected loader length to exceed error threshold")
    else:
        if is_iterable_dataset:
            if len(ds) <= error_it + 1:
                raise AssertionError(
                    "Expected iterable dataset length to exceed error threshold"
                )
        else:
            if len(loader) <= error_it + 1:
                raise AssertionError("Expected loader length to exceed error threshold")

    it = iter(loader)
    if use_workers:
        workers = it._workers

    def kill_pid(pid):
        psutil_p = psutil.Process(pid)
        psutil_p.kill()
        psutil_p.wait(JOIN_TIMEOUT)
        if psutil_p.is_running():
            raise AssertionError("Expected process to be terminated")

    for i, _ in enumerate(it):
        if i == 0:
            if not hold_iter_reference:
                del it
                del loader
            loader_setup_event.set()
            tester_setup_event.wait()
            # ensure that the workers are still alive
            if use_workers:
                for w in workers:
                    if not w.is_alive():
                        raise AssertionError("Expected worker process to be alive")
            if worker_error_event is not None:
                worker_error_event.set()

        if i == error_it:
            if exit_method == "loader_error":
                raise RuntimeError("Loader error")
            elif exit_method == "loader_kill":
                kill_pid(os.getpid())
            elif exit_method == "worker_kill":
                kill_pid(workers[-1].pid)  # kill last worker

    if not hold_iter_reference:
        # Tries to trigger the __del__ clean-up rather than the automatic
        # exiting of daemonic children. Technically it should be automatically
        # triggered, but I don't want to rely on the implementation detail of
        # Python gc.
        gc.collect()