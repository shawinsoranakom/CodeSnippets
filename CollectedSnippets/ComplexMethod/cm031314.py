def close(self):
        if self._iocp is None:
            # already closed
            return

        # Cancel remaining registered operations.
        for fut, ov, obj, callback in list(self._cache.values()):
            if fut.cancelled():
                # Nothing to do with cancelled futures
                pass
            elif isinstance(fut, _WaitCancelFuture):
                # _WaitCancelFuture must not be cancelled
                pass
            else:
                try:
                    fut.cancel()
                except OSError as exc:
                    if self._loop is not None:
                        context = {
                            'message': 'Cancelling a future failed',
                            'exception': exc,
                            'future': fut,
                        }
                        if fut._source_traceback:
                            context['source_traceback'] = fut._source_traceback
                        self._loop.call_exception_handler(context)

        # Wait until all cancelled overlapped complete: don't exit with running
        # overlapped to prevent a crash. Display progress every second if the
        # loop is still running.
        msg_update = 1.0
        start_time = time.monotonic()
        next_msg = start_time + msg_update
        while self._cache:
            if next_msg <= time.monotonic():
                logger.debug('%r is running after closing for %.1f seconds',
                             self, time.monotonic() - start_time)
                next_msg = time.monotonic() + msg_update

            # handle a few events, or timeout
            self._poll(msg_update)

        self._results = []

        _winapi.CloseHandle(self._iocp)
        self._iocp = None