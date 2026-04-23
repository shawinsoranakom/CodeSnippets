def map(self, fn, *iterables, timeout=None, chunksize=1, buffersize=None):
        """Returns an iterator equivalent to map(fn, iter).

        Args:
            fn: A callable that will take as many arguments as there are
                passed iterables.
            timeout: The maximum number of seconds to wait. If None, then there
                is no limit on the wait time.
            chunksize: The size of the chunks the iterable will be broken into
                before being passed to a child process. This argument is only
                used by ProcessPoolExecutor; it is ignored by
                ThreadPoolExecutor.
            buffersize: The number of submitted tasks whose results have not
                yet been yielded. If the buffer is full, iteration over the
                iterables pauses until a result is yielded from the buffer.
                If None, all input elements are eagerly collected, and a task is
                submitted for each.

        Returns:
            An iterator equivalent to: map(func, *iterables) but the calls may
            be evaluated out-of-order.

        Raises:
            TimeoutError: If the entire result iterator could not be generated
                before the given timeout.
            Exception: If fn(*args) raises for any values.
        """
        if buffersize is not None and not isinstance(buffersize, int):
            raise TypeError("buffersize must be an integer or None")
        if buffersize is not None and buffersize < 1:
            raise ValueError("buffersize must be None or > 0")

        if timeout is not None:
            end_time = timeout + time.monotonic()

        zipped_iterables = zip(*iterables)
        if buffersize:
            fs = collections.deque(
                self.submit(fn, *args) for args in islice(zipped_iterables, buffersize)
            )
        else:
            fs = [self.submit(fn, *args) for args in zipped_iterables]

        # Use a weak reference to ensure that the executor can be garbage
        # collected independently of the result_iterator closure.
        executor_weakref = weakref.ref(self)

        # Yield must be hidden in closure so that the futures are submitted
        # before the first iterator value is required.
        def result_iterator():
            try:
                # reverse to keep finishing order
                fs.reverse()
                while fs:
                    if (
                        buffersize
                        and (executor := executor_weakref())
                        and (args := next(zipped_iterables, None))
                    ):
                        fs.appendleft(executor.submit(fn, *args))
                    # Careful not to keep a reference to the popped future
                    if timeout is None:
                        yield _result_or_cancel(fs.pop())
                    else:
                        yield _result_or_cancel(fs.pop(), end_time - time.monotonic())
            finally:
                for future in fs:
                    future.cancel()
        return result_iterator()