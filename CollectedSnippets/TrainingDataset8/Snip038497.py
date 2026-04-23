def debug(self):
        self._setupAsyncioLoop()
        super().debug()
        self._tearDownAsyncioLoop()