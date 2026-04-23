def read(self, size=-1):
        """Read at most size bytes from the chunk.
        If size is omitted or negative, read until the end
        of the chunk.
        """

        if self.closed:
            raise ValueError("I/O operation on closed file")
        if self.size_read >= self.chunksize:
            return b''
        if size < 0:
            size = self.chunksize - self.size_read
        if size > self.chunksize - self.size_read:
            size = self.chunksize - self.size_read
        data = self.file.read(size)
        self.size_read = self.size_read + len(data)
        if self.size_read == self.chunksize and \
           self.align and \
           (self.chunksize & 1):
            dummy = self.file.read(1)
            self.size_read = self.size_read + len(dummy)
        return data