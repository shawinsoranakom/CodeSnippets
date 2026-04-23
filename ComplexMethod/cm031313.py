def _poll(self, timeout=None):
        if timeout is None:
            ms = INFINITE
        elif timeout < 0:
            raise ValueError("negative timeout")
        else:
            # GetQueuedCompletionStatus() has a resolution of 1 millisecond,
            # round away from zero to wait *at least* timeout seconds.
            ms = math.ceil(timeout * 1e3)
            if ms >= INFINITE:
                raise ValueError("timeout too big")

        while True:
            status = _overlapped.GetQueuedCompletionStatus(self._iocp, ms)
            if status is None:
                break
            ms = 0

            err, transferred, key, address = status
            try:
                f, ov, obj, callback = self._cache.pop(address)
            except KeyError:
                if self._loop.get_debug():
                    self._loop.call_exception_handler({
                        'message': ('GetQueuedCompletionStatus() returned an '
                                    'unexpected event'),
                        'status': ('err=%s transferred=%s key=%#x address=%#x'
                                   % (err, transferred, key, address)),
                    })

                # key is either zero, or it is used to return a pipe
                # handle which should be closed to avoid a leak.
                if key not in (0, _overlapped.INVALID_HANDLE_VALUE):
                    _winapi.CloseHandle(key)
                continue

            if obj in self._stopped_serving:
                f.cancel()
            # Don't call the callback if _register() already read the result or
            # if the overlapped has been cancelled
            elif not f.done():
                try:
                    value = callback(transferred, key, ov)
                except OSError as e:
                    f.set_exception(e)
                    self._results.append(f)
                else:
                    f.set_result(value)
                    self._results.append(f)
                finally:
                    f = None

        # Remove unregistered futures
        for ov in self._unregistered:
            self._cache.pop(ov.address, None)
        self._unregistered.clear()