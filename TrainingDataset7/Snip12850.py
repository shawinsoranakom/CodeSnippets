def __init__(self, producer, length=None):
        """
        Every LazyStream must have a producer when instantiated.

        A producer is an iterable that returns a string each time it
        is called.
        """
        self._producer = producer
        self._empty = False
        self._leftover = b""
        self.length = length
        self.position = 0
        self._remaining = length
        self._unget_history = []