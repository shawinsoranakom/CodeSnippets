def call_on_threads(
    func: Callable[[int], Any], num_threads: int, timeout: Optional[float] = 0.25
) -> None:
    """Call a function on multiple threads simultaneously and assert that no
    thread raises an unhandled exception.

    The function must take single `int` param, which will be the index of
    the thread it's being called on.

    Note that a passing multi-threaded test does not generally guarantee that
    the tested code is thread safe! Because threading issues tend to be
    non-deterministic, a flaky test that fails only occasionally is a good
    indicator of an underlying issue.
    """
    threads = [
        ExceptionCapturingThread(name=f"Thread {ii}", target=func, args=[ii])
        for ii in range(num_threads)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=timeout)
        thread.assert_no_unhandled_exception()