def has_curve(self):
        """Return True if the geometry is or has curve geometry."""
        return capi.has_curve_geom(self.ptr, 0)