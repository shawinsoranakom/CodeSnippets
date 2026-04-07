def __next__(self):
        """
        Used when the exact number of bytes to read is unimportant.

        Return whatever chunk is conveniently returned from the iterator.
        Useful to avoid unnecessary bookkeeping if performance is an issue.
        """
        if self._leftover:
            output = self._leftover
            self._leftover = b""
        else:
            output = next(self._producer)
            self._unget_history = []
        self.position += len(output)
        return output