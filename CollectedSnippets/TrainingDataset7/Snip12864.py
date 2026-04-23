def __init__(self, stream, boundary):
        self._stream = stream
        self._boundary = boundary
        self._done = False
        # rollback an additional six bytes because the format is like
        # this: CRLF<boundary>[--CRLF]
        self._rollback = len(boundary) + 6

        # Try to use mx fast string search if available. Otherwise
        # use Python find. Wrap the latter for consistency.
        unused_char = self._stream.read(1)
        if not unused_char:
            raise InputStreamExhausted()
        self._stream.unget(unused_char)