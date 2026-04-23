def write(self, geom):
        "Return the WKT representation of the given geometry."
        return wkt_writer_write(self.ptr, geom.ptr)