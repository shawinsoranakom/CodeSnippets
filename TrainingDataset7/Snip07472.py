def write_hex(self, geom):
        "Return the HEXEWKB representation of the given geometry."
        geom = self._handle_empty_point(geom)
        wkb = wkb_writer_write_hex(self.ptr, geom.ptr, byref(c_size_t()))
        return wkb