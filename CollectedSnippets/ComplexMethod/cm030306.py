def wait(fs, timeout=None, return_when=ALL_COMPLETED):
    """Wait for the futures in the given sequence to complete.

    Args:
        fs: The sequence of Futures (possibly created by different Executors) to
            wait upon.
        timeout: The maximum number of seconds to wait. If None, then there
            is no limit on the wait time.
        return_when: Indicates when this function should return. The options
            are:

            FIRST_COMPLETED - Return when any future finishes or is
                              cancelled.
            FIRST_EXCEPTION - Return when any future finishes by raising an
                              exception. If no future raises an exception
                              then it is equivalent to ALL_COMPLETED.
            ALL_COMPLETED -   Return when all futures finish or are cancelled.

    Returns:
        A named 2-tuple of sets. The first set, named 'done', contains the
        futures that completed (is finished or cancelled) before the wait
        completed. The second set, named 'not_done', contains uncompleted
        futures. Duplicate futures given to *fs* are removed and will be
        returned only once.
    """
    fs = set(fs)
    with _AcquireFutures(fs):
        done = {f for f in fs
                   if f._state in [CANCELLED_AND_NOTIFIED, FINISHED]}
        not_done = fs - done
        if (return_when == FIRST_COMPLETED) and done:
            return DoneAndNotDoneFutures(done, not_done)
        elif (return_when == FIRST_EXCEPTION) and done:
            if any(f for f in done
                   if not f.cancelled() and f.exception() is not None):
                return DoneAndNotDoneFutures(done, not_done)

        if len(done) == len(fs):
            return DoneAndNotDoneFutures(done, not_done)

        waiter = _create_and_install_waiters(fs, return_when)

    waiter.event.wait(timeout)
    for f in fs:
        with f._condition:
            f._waiters.remove(waiter)

    done.update(waiter.finished_futures)
    return DoneAndNotDoneFutures(done, fs - done)