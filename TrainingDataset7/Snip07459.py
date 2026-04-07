def read(self, wkt):
        if not isinstance(wkt, (bytes, str)):
            raise TypeError(f"'wkt' must be bytes or str (got {wkt!r} instead).")
        return wkt_reader_read(self.ptr, force_bytes(wkt))