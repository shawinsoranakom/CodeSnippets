def __del__(self):
        if self._asyncioTestLoop is not None:
            self._tearDownAsyncioLoop()