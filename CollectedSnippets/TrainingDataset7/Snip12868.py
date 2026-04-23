def __init__(self, stream, boundary):
        self._stream = stream
        self._separator = b"--" + boundary