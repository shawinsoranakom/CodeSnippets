def close(self):
        """Close the _Stream object. No operation should be
           done on it afterwards.
        """
        if self.closed:
            return

        self.closed = True
        try:
            if self.mode == "w" and self.comptype != "tar":
                self.buf += self.cmp.flush()

            if self.mode == "w" and self.buf:
                self.fileobj.write(self.buf)
                self.buf = b""
                if self.comptype == "gz":
                    self.fileobj.write(struct.pack("<L", self.crc))
                    self.fileobj.write(struct.pack("<L", self.pos & 0xffffFFFF))
        finally:
            if not self._extfileobj:
                self.fileobj.close()