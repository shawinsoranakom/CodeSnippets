def get_curve_geometry(self):
        """Return a curve version of this geometry."""
        return OGRGeometry(capi.get_curve_geom(self.ptr, None))