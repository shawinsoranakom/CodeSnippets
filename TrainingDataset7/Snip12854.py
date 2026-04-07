def close(self):
        """
        Used to invalidate/disable this lazy stream.

        Replace the producer with an empty list. Any leftover bytes that have
        already been read will still be reported upon read() and/or next().
        """
        self._producer = []