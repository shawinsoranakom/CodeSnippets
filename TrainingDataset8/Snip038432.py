def initialize(self, callback):
        """Initialize the handler

        Parameters
        ----------
        callback : callable
            A function that returns True if the server is healthy

        """
        self._callback = callback