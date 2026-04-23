def read(self, size=None):
        """Read data from the file.
        """
        if size is None:
            size = self.size - self.position
        else:
            size = min(size, self.size - self.position)

        buf = b""
        while size > 0:
            while True:
                data, start, stop, offset = self.map[self.map_index]
                if start <= self.position < stop:
                    break
                else:
                    self.map_index += 1
                    if self.map_index == len(self.map):
                        self.map_index = 0
            length = min(size, stop - self.position)
            if data:
                self.fileobj.seek(offset + (self.position - start))
                b = self.fileobj.read(length)
                if len(b) != length:
                    raise ReadError("unexpected end of data")
                buf += b
            else:
                buf += NUL * length
            size -= length
            self.position += length
        return buf