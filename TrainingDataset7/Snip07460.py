def read(self, wkb):
        "Return a _pointer_ to C GEOS Geometry object from the given WKB."
        if isinstance(wkb, memoryview):
            wkb_s = bytes(wkb)
            return wkb_reader_read(self.ptr, wkb_s, len(wkb_s))
        elif isinstance(wkb, bytes):
            return wkb_reader_read_hex(self.ptr, wkb, len(wkb))
        elif isinstance(wkb, str):
            wkb_s = wkb.encode()
            return wkb_reader_read_hex(self.ptr, wkb_s, len(wkb_s))
        else:
            raise TypeError(
                f"'wkb' must be bytes, str or memoryview (got {wkb!r} instead)."
            )