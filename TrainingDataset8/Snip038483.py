def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self._asyncioTestLoop = None
        self._asyncioCallsQueue = None