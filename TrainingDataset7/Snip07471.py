def write(self, geom):
        "Return the WKB representation of the given geometry."
        geom = self._handle_empty_point(geom)
        wkb = wkb_writer_write(self.ptr, geom.ptr, byref(c_size_t()))
        return memoryview(wkb)