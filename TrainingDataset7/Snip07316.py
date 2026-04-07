def boundary(self):
        "Return the boundary as a newly allocated Geometry object."
        return self._topology(capi.geos_boundary(self.ptr))