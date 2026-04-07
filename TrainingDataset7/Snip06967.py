def get_linear_geometry(self):
        """Return a linear version of this geometry."""
        return OGRGeometry(capi.get_linear_geom(self.ptr, 0, None))