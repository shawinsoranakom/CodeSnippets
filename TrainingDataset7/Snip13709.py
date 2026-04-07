def get_max_test_processes():
    """
    The maximum number of test processes when using the --parallel option.
    """
    # The current implementation of the parallel test runner requires
    # multiprocessing to start subprocesses with fork(), forkserver(), or
    # spawn().
    if multiprocessing.get_start_method() not in {"fork", "spawn", "forkserver"}:
        return 1
    try:
        return int(os.environ["DJANGO_TEST_PROCESSES"])
    except KeyError:
        return multiprocessing.cpu_count()