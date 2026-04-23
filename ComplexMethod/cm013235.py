def run_concurrently(worker_func, num_threads=None, args=(), kwargs=None):
    # Adapted from CPython test suite. Runs worker_func in multiple threads
    # concurrently to help expose thread-safety issues. Works best in
    # combination with ThreadSanitizer (TSan).
    from collections.abc import Iterable

    if kwargs is None:
        kwargs = {}
    if num_threads is None:
        num_threads = len(worker_func)
    if not isinstance(worker_func, Iterable):
        worker_func = [worker_func] * num_threads

    barrier = threading.Barrier(num_threads)

    results = [None] * num_threads
    exc_value = None

    def wrapper_func(idx, func, *args, **kwargs):
        # Wait for all threads to reach this point before proceeding.
        try:
            barrier.wait()
            res = func(*args, **kwargs)
            results[idx] = res
        except Exception as e:
            nonlocal exc_value
            exc_value = e

    workers = [
        threading.Thread(target=wrapper_func, args=(i, func, *args),
                         kwargs=kwargs, daemon=True)
        for i, func in enumerate(worker_func)
    ]
    for w in workers:
        w.start()
    for w in workers:
        w.join()

    # If a worker thread raises an exception, re-raise it.
    if exc_value is not None:
        raise exc_value

    return results