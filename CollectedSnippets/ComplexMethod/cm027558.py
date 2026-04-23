def read(self, n: int = -1, /) -> bytes:
        """Read up to n bytes of data from the iterator.

        The read method returns 0 bytes when the iterator is exhausted.
        """
        result = bytearray()
        while n < 0 or len(result) < n:
            if self._exhausted:
                break
            if not self._buffer:
                self._next_future = asyncio.run_coroutine_threadsafe(
                    self._next(), self._loop
                )
                if self._aborted:
                    self._next_future.cancel()
                    raise Abort
                try:
                    self._buffer = self._next_future.result()
                except CancelledError as err:
                    raise Abort from err
                self._pos = 0
            if not self._buffer:
                # The stream is exhausted
                self._exhausted = True
                break
            chunk = self._buffer[self._pos : self._pos + n]
            result.extend(chunk)
            n -= len(chunk)
            self._pos += len(chunk)
            if self._pos == len(self._buffer):
                self._buffer = None
        return bytes(result)