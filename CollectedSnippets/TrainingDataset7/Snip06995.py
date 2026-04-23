def _geomgen(self, gen_func, other=None):
        "A helper routine for the OGR routines that generate geometries."
        if isinstance(other, OGRGeometry):
            return OGRGeometry(gen_func(self.ptr, other.ptr), self.srs)
        else:
            return OGRGeometry(gen_func(self.ptr), self.srs)