def get(self, block=True, timeout=None, *,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Return the next object from the queue.

        If "block" is true, this blocks while the queue is empty.

        If the next item's original interpreter has been destroyed
        then the "next object" is determined by the value of the
        "unbounditems" argument to put().
        """
        if not block:
            return self.get_nowait()
        if timeout is not None:
            timeout = int(timeout)
            if timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        while True:
            try:
                obj, unboundop = _queues.get(self._id)
            except QueueEmpty:
                if timeout is not None and time.time() >= end:
                    raise  # re-raise
                time.sleep(_delay)
            else:
                break
        if unboundop is not None:
            assert obj is None, repr(obj)
            return _resolve_unbound(unboundop)
        return obj