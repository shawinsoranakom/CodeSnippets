def read(self, size=None):
        def parts():
            remaining = self._remaining if size is None else size
            # do the whole thing in one shot if no limit was provided.
            if remaining is None:
                yield b"".join(self)
                return

            # otherwise do some bookkeeping to return exactly enough
            # of the stream and stashing any extra content we get from
            # the producer
            while remaining != 0:
                assert remaining > 0, "remaining bytes to read should never go negative"

                try:
                    chunk = next(self)
                except StopIteration:
                    return
                else:
                    emitting = chunk[:remaining]
                    self.unget(chunk[remaining:])
                    remaining -= len(emitting)
                    yield emitting

        return b"".join(parts())