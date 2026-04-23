def get(self, block=True, timeout=None):
        if self._closed:
            raise ValueError(f"Queue {self!r} is closed")
        if block and timeout is None:
            with self._rlock:
                res = self._recv_bytes()
            self._sem.release()
        else:
            if block:
                deadline = time.monotonic() + timeout
            if not self._rlock.acquire(block, timeout):
                raise Empty
            try:
                if block:
                    timeout = deadline - time.monotonic()
                    if not self._poll(timeout):
                        raise Empty
                elif not self._poll():
                    raise Empty
                res = self._recv_bytes()
                self._sem.release()
            finally:
                self._rlock.release()
        # unserialize the data after having released the lock
        return _ForkingPickler.loads(res)