def recv(self, timeout=None, *,
             _sentinel=object(),
             _delay=10 / 1000,  # 10 milliseconds
             ):
        """Return the next object from the channel.

        This blocks until an object has been sent, if none have been
        sent already.
        """
        if timeout is not None:
            timeout = int(timeout)
            if timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        obj, unboundop = _channels.recv(self._id, _sentinel)
        while obj is _sentinel:
            time.sleep(_delay)
            if timeout is not None and time.time() >= end:
                raise TimeoutError
            obj, unboundop = _channels.recv(self._id, _sentinel)
        if unboundop is not None:
            assert obj is None, repr(obj)
            return _resolve_unbound(unboundop)
        return obj