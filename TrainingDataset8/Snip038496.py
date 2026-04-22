def run(self, result=None):
        self._setupAsyncioLoop()
        try:
            return super().run(result)
        finally:
            self._tearDownAsyncioLoop()