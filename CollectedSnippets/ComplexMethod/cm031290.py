def _force_close(self, exc):
        if self._empty_waiter is not None and not self._empty_waiter.done():
            if exc is None:
                self._empty_waiter.set_result(None)
            else:
                self._empty_waiter.set_exception(exc)
        if self._closing and self._called_connection_lost:
            return
        self._closing = True
        self._conn_lost += 1
        if self._write_fut:
            self._write_fut.cancel()
            self._write_fut = None
        if self._read_fut:
            self._read_fut.cancel()
            self._read_fut = None
        self._pending_write = 0
        self._buffer = None
        self._loop.call_soon(self._call_connection_lost, exc)