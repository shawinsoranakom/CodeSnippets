def __next__(self):
        if self._done:
            raise StopIteration()

        stream = self._stream
        rollback = self._rollback

        bytes_read = 0
        chunks = []
        for bytes in stream:
            bytes_read += len(bytes)
            chunks.append(bytes)
            if bytes_read > rollback:
                break
            if not bytes:
                break
        else:
            self._done = True

        if not chunks:
            raise StopIteration()

        chunk = b"".join(chunks)
        boundary = self._find_boundary(chunk)

        if boundary:
            end, next = boundary
            stream.unget(chunk[next:])
            self._done = True
            return chunk[:end]
        else:
            # make sure we don't treat a partial boundary (and
            # its separators) as data
            if not chunk[:-rollback]:  # and len(chunk) >= (len(self._boundary) + 6):
                # There's nothing left, we should just return and mark as done.
                self._done = True
                return chunk
            else:
                stream.unget(chunk[-rollback:])
                return chunk[:-rollback]