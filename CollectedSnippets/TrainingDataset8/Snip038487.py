def _callSetUp(self):
        self.setUp()
        self._callAsync(self.asyncSetUp)